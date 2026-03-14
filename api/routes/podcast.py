"""Podcast routes: browse, add, delete podcasts; list episodes; transcribe."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from api.dependencies import get_current_user_id, get_supabase
from api.services.podcast_service import (
    STARTER_PODCASTS,
    parse_rss_feed,
    parse_episodes_from_feed,
    transcribe_audio,
)
from api.config import get_settings

router = APIRouter(prefix="/api/podcasts", tags=["podcasts"])


class AddPodcastRequest(BaseModel):
    rss_url: str
    language: str


class TranscribeRequest(BaseModel):
    guid: str
    title: str
    audio_url: str
    duration: Optional[int] = None
    published_at: Optional[str] = None


@router.get("")
def list_podcasts(
    language: str = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_supabase),
):
    """List user's podcasts for a language. Auto-seeds starters if none exist."""
    # If no language param, fall back to user's last_language
    if not language:
        settings = db.table("user_settings").select("last_language").eq("user_id", user_id).maybe_single().execute()
        language = settings.data.get("last_language", "") if settings.data else ""

    # Seed starters for this language if user has none for it
    if language and language in STARTER_PODCASTS:
        existing = db.table("podcasts").select("id").eq("user_id", user_id).eq("language", language).execute()
        if not existing.data:
            for starter in STARTER_PODCASTS[language]:
                try:
                    # Fetch RSS to get real image URL (CDN-hosted, CORS-friendly)
                    metadata = parse_rss_feed(starter["rss_url"])
                    db.table("podcasts").insert({
                        "user_id": user_id,
                        "title": metadata["title"] or starter["title"],
                        "description": metadata["description"] or starter.get("description", ""),
                        "rss_url": starter["rss_url"],
                        "image_url": metadata["image_url"],
                        "language": language,
                        "is_starter": True,
                    }).execute()
                except Exception as e:
                    print(f"Failed to seed starter '{starter['title']}': {e}")

    # Filter by language
    query = db.table("podcasts").select("*").eq("user_id", user_id).order("created_at")
    if language:
        query = query.eq("language", language)
    result = query.execute()
    return {"podcasts": result.data}


@router.post("")
def add_podcast(
    body: AddPodcastRequest,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_supabase),
):
    """Add a podcast from RSS URL."""
    try:
        metadata = parse_rss_feed(body.rss_url)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not parse RSS feed")

    result = db.table("podcasts").insert({
        "user_id": user_id,
        "title": metadata["title"],
        "description": metadata["description"],
        "rss_url": body.rss_url,
        "image_url": metadata["image_url"],
        "language": body.language,
        "is_starter": False,
    }).execute()

    return result.data[0]


@router.delete("/{podcast_id}")
def delete_podcast(
    podcast_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_supabase),
):
    """Delete a podcast and its episodes (cascade)."""
    result = db.table("podcasts").delete().eq("id", podcast_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Podcast not found")
    return {"ok": True}


@router.get("/{podcast_id}/episodes")
def list_episodes(
    podcast_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_supabase),
):
    """List episodes from RSS feed, merging transcription status from DB."""
    podcast = db.table("podcasts").select("rss_url").eq("id", podcast_id).eq("user_id", user_id).maybe_single().execute()
    if not podcast.data:
        raise HTTPException(status_code=404, detail="Podcast not found")

    try:
        episodes = parse_episodes_from_feed(podcast.data["rss_url"])
    except Exception:
        raise HTTPException(status_code=400, detail="Could not fetch podcast feed")

    transcribed = db.table("podcast_episodes").select("guid, id").eq("podcast_id", podcast_id).eq("is_transcribed", True).execute()
    transcribed_map = {row["guid"]: row["id"] for row in (transcribed.data or [])}

    for ep in episodes:
        ep["is_transcribed"] = ep["guid"] in transcribed_map
        ep["episode_id"] = transcribed_map.get(ep["guid"])

    return {"episodes": episodes}


@router.post("/{podcast_id}/episodes/transcribe")
def transcribe_episode(
    podcast_id: str,
    body: TranscribeRequest,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_supabase),
):
    """Transcribe an episode using Whisper API."""
    podcast = db.table("podcasts").select("id").eq("id", podcast_id).eq("user_id", user_id).maybe_single().execute()
    if not podcast.data:
        raise HTTPException(status_code=404, detail="Podcast not found")

    api_key = get_settings().openai_api_key
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")

    try:
        segments = transcribe_audio(body.audio_url, api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Transcription failed")

    result = db.table("podcast_episodes").upsert({
        "podcast_id": podcast_id,
        "guid": body.guid,
        "title": body.title,
        "audio_url": body.audio_url,
        "duration": body.duration,
        "published_at": body.published_at,
        "transcript": segments,
        "is_transcribed": True,
    }, on_conflict="podcast_id,guid").execute()

    return result.data[0]


@router.get("/{podcast_id}/episodes/{episode_id}")
def get_episode(
    podcast_id: str,
    episode_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_supabase),
):
    """Get a transcribed episode with its transcript."""
    result = (
        db.table("podcast_episodes")
        .select("*, podcasts!inner(user_id)")
        .eq("id", episode_id)
        .eq("podcast_id", podcast_id)
        .eq("podcasts.user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Episode not found")

    episode = {k: v for k, v in result.data.items() if k != "podcasts"}
    return episode
