import pytest
from unittest.mock import patch, MagicMock
from api.services.podcast_service import (
    STARTER_PODCASTS,
    parse_rss_feed,
    parse_episodes_from_feed,
)


def test_starter_podcasts_has_all_languages():
    for lang in ["fr", "es", "it", "ru", "zh"]:
        assert lang in STARTER_PODCASTS
        assert len(STARTER_PODCASTS[lang]) >= 1
        for pod in STARTER_PODCASTS[lang]:
            assert "title" in pod
            assert "rss_url" in pod


def test_parse_rss_feed_extracts_metadata():
    mock_feed = MagicMock()
    mock_feed.feed.get.side_effect = lambda k, d="": {
        "title": "My Podcast",
        "subtitle": "A great podcast",
        "image": MagicMock(href="https://example.com/cover.jpg"),
    }.get(k, d)

    with patch("api.services.podcast_service.feedparser.parse", return_value=mock_feed):
        result = parse_rss_feed("https://example.com/feed.xml")

    assert result["title"] == "My Podcast"
    assert "cover.jpg" in result["image_url"]


def test_parse_episodes_from_feed():
    mock_entry = MagicMock()
    links = [{"rel": "enclosure", "href": "https://example.com/ep1.mp3", "type": "audio/mpeg"}]
    mock_entry.get.side_effect = lambda k, d=None: {
        "id": "ep-guid-1",
        "title": "Episode 1",
        "summary": "Ep description",
        "links": links,
        "published_parsed": None,
    }.get(k, d)

    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]

    with patch("api.services.podcast_service.feedparser.parse", return_value=mock_feed):
        episodes = parse_episodes_from_feed("https://example.com/feed.xml")

    assert len(episodes) >= 1
    assert episodes[0]["title"] == "Episode 1"
    assert episodes[0]["audio_url"] == "https://example.com/ep1.mp3"
    assert episodes[0]["guid"] == "ep-guid-1"


def test_transcribe_audio_rejects_large_files():
    mock_response = MagicMock()
    mock_response.headers = {"content-length": str(30 * 1024 * 1024)}

    with patch("api.services.podcast_service.requests.head", return_value=mock_response):
        with pytest.raises(ValueError, match="too large"):
            from api.services.podcast_service import transcribe_audio
            transcribe_audio("https://example.com/huge.mp3", "fake-key")
