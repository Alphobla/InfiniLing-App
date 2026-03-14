"""Podcast service: RSS parsing, Whisper transcription, starter podcast config."""

import tempfile
import os
from datetime import datetime
from calendar import timegm

import feedparser
import requests
from openai import OpenAI


STARTER_PODCASTS = {
    "fr": [
        {
            "title": "Tout un monde",
            "rss_url": "https://feeds.rts.ch/info-tout-un-monde.xml",
            "image_url": "https://www.rts.ch/2024/06/28/17/31/14928029.image/16x9",
            "description": "RTS — Actualité internationale",
        },
        {
            "title": "Journal en français facile",
            "rss_url": "https://savoirs.rfi.fr/fr/apprendre-enseigner/langue-francaise/journal-en-francais-facile/podcast",
            "image_url": "",
            "description": "RFI — Actualité simplifiée",
        },
        {
            "title": "InnerFrench",
            "rss_url": "https://feeds.soundcloud.com/users/soundcloud:users:304682547/sounds.rss",
            "image_url": "",
            "description": "Hugo Cotton — Intermediate French",
        },
    ],
    "es": [
        {
            "title": "News in Slow Spanish",
            "rss_url": "https://www.newsinslowspanish.com/latino/podcast/feed",
            "image_url": "",
            "description": "Current events in slow Spanish",
        },
    ],
    "it": [
        {
            "title": "News in Slow Italian",
            "rss_url": "https://www.newsinslowitalian.com/podcast/feed",
            "image_url": "",
            "description": "Current events in slow Italian",
        },
    ],
    "ru": [
        {
            "title": "Russian Podcast",
            "rss_url": "https://russianpodcast.eu/feed/podcast",
            "image_url": "",
            "description": "Slow Russian for learners",
        },
    ],
    "zh": [
        {
            "title": "ChinesePod",
            "rss_url": "https://chinesepod.com/feed",
            "image_url": "",
            "description": "Learn Mandarin Chinese",
        },
    ],
}


def parse_rss_feed(rss_url: str) -> dict:
    """Parse an RSS feed URL and return podcast metadata."""
    feed = feedparser.parse(rss_url)
    title = feed.feed.get("title", "Unknown Podcast")
    description = feed.feed.get("subtitle", "") or feed.feed.get("summary", "")

    image_url = ""
    image = feed.feed.get("image")
    if image and hasattr(image, "href"):
        image_url = image.href

    return {"title": title, "description": description, "image_url": image_url}


def parse_episodes_from_feed(rss_url: str, limit: int = 50) -> list[dict]:
    """Parse RSS feed and return list of episode dicts."""
    feed = feedparser.parse(rss_url)
    episodes = []

    for entry in feed.entries[:limit]:
        audio_url = ""
        for link in entry.get("links", []):
            if link.get("rel") == "enclosure" and "audio" in link.get("type", ""):
                audio_url = link.get("href", "")
                break

        if not audio_url:
            continue

        duration = None
        raw_duration = entry.get("itunes_duration")
        if raw_duration:
            try:
                if ":" in str(raw_duration):
                    parts = str(raw_duration).split(":")
                    if len(parts) == 3:
                        duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    elif len(parts) == 2:
                        duration = int(parts[0]) * 60 + int(parts[1])
                else:
                    duration = int(raw_duration)
            except (ValueError, TypeError):
                pass

        published_at = None
        published_parsed = entry.get("published_parsed")
        if published_parsed:
            try:
                published_at = datetime.utcfromtimestamp(timegm(published_parsed)).isoformat()
            except (ValueError, TypeError, OverflowError):
                pass

        episodes.append({
            "guid": entry.get("id", entry.get("link", "")),
            "title": entry.get("title", "Untitled"),
            "description": entry.get("summary", ""),
            "audio_url": audio_url,
            "duration": duration,
            "published_at": published_at,
        })

    return episodes


def transcribe_audio(audio_url: str, api_key: str) -> list[dict]:
    """Download audio from URL and transcribe with OpenAI Whisper."""
    head = requests.head(audio_url, allow_redirects=True, timeout=10)
    content_length = int(head.headers.get("content-length", 0))
    if content_length > 25 * 1024 * 1024:
        raise ValueError(f"Audio file too large ({content_length // (1024*1024)}MB). Whisper API limit is 25MB.")

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    try:
        response = requests.get(audio_url, stream=True, timeout=300)
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp.close()

        client = OpenAI(api_key=api_key)
        with open(tmp.name, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        segments = []
        for seg in result.segments:
            segments.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
            })

        return segments

    finally:
        os.unlink(tmp.name)
