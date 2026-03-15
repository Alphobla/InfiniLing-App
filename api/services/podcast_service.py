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
        {"title": "Tout un monde", "rss_url": "https://www.rts.ch/rts-premiere/programmes/tout-un-monde/podcast/?flux=rss"},
        {"title": "InnerFrench", "rss_url": "https://podcast.innerfrench.com/feed.xml"},
        {"title": "Français Authentique", "rss_url": "https://francaisauthentique.libsyn.com/rss"},
    ],
    "es": [
        {"title": "Hoy Hablamos", "rss_url": "https://hoyhablamos.com/feed/"},
        {"title": "Español Automático", "rss_url": "https://espanolautomatico.libsyn.com/rss"},
    ],
    "ru": [
        {"title": "Russian Made Easy", "rss_url": "https://russianmadeeasy.com/feed/podcast/"},
        {"title": "Slow Russian", "rss_url": "https://slowrussian.libsyn.com/rss"},
        {"title": "Comprehensible Russian (Russian With Max)", "rss_url": "https://anchor.fm/s/6f65684/podcast/rss"},
        {"title": "Русский Подкаст (Tatiana Klimova)", "rss_url": "https://russianpodcast.eu/feed"},
        {"title": "Be Fluent in Russian", "rss_url": "https://rss.buzzsprout.com/1861558.rss"},
    ],
}


def parse_rss_feed(rss_url: str) -> dict:
    """Parse an RSS feed URL and return podcast metadata."""
    feed = feedparser.parse(rss_url)
    title = feed.feed.get("title", "Unknown Podcast")
    description = feed.feed.get("subtitle", "") or feed.feed.get("summary", "")

    # Try itunes:image first (most common), then standard RSS <image>
    image_url = ""
    itunes_image = feed.feed.get("image")
    if itunes_image and hasattr(itunes_image, "href"):
        image_url = itunes_image.href
    if not image_url:
        # feedparser stores <itunes:image href="..."> under a different key
        itunes_img = feed.feed.get("itunes_image")
        if itunes_img and hasattr(itunes_img, "href"):
            image_url = itunes_img.href

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


def _compress_audio(input_path: str) -> str:
    """
    Compress an audio file to mono 32kbps MP3 using the ffmpeg binary bundled
    inside the `imageio-ffmpeg` Python package.

    Why imageio-ffmpeg: Vercel (and other serverless platforms) don't let you
    install system packages. imageio-ffmpeg ships a pre-built ffmpeg binary
    as part of the pip wheel, so it works anywhere Python packages are installed.

    Why compress: Whisper has a 25 MB limit. At 32kbps mono, 20 min ≈ 4.8 MB.
    Whisper transcription quality is not affected by bitrate reduction.
    """
    import subprocess
    import imageio_ffmpeg  # provides get_ffmpeg_exe() → path to bundled binary

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    compressed = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    compressed.close()
    subprocess.run(
        [
            ffmpeg_exe, "-y",        # -y = overwrite output without asking
            "-i", input_path,        # input file
            "-ac", "1",              # mono (1 audio channel)
            "-ar", "16000",          # 16 kHz sample rate (Whisper's native rate)
            "-b:a", "32k",           # 32 kbps bitrate
            compressed.name,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return compressed.name


def transcribe_audio(audio_url: str, api_key: str) -> list[dict]:
    """Download audio from URL and transcribe with OpenAI Whisper.

    If the file exceeds Whisper's 25 MB limit, it is compressed with ffmpeg
    before being sent (see _compress_audio).
    """
    WHISPER_LIMIT = 25 * 1024 * 1024  # 25 MB

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    compressed_path = None
    try:
        # Download the audio
        response = requests.get(audio_url, stream=True, timeout=300)
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp.close()

        audio_path = tmp.name

        # Compress if needed
        if os.path.getsize(audio_path) > WHISPER_LIMIT:
            compressed_path = _compress_audio(audio_path)
            audio_path = compressed_path

        client = OpenAI(api_key=api_key)
        with open(audio_path, "rb") as audio_file:
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
        if compressed_path:
            os.unlink(compressed_path)
