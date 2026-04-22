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


import requests
from api.services.podcast_service import search_itunes_podcasts


def _make_itunes_response(results):
    """Build a fake requests.Response.json() payload from iTunes."""
    mock = MagicMock()
    mock.json.return_value = {"resultCount": len(results), "results": results}
    mock.raise_for_status.return_value = None
    return mock


def test_search_itunes_podcasts_passes_country_for_known_language():
    """Polish search must include country=PL so results are biased to Polish shows."""
    response = _make_itunes_response([
        {
            "collectionName": "Easy Polish",
            "artistName": "Easy Languages",
            "feedUrl": "https://example.com/feed.xml",
            "artworkUrl600": "https://example.com/cover.jpg",
        }
    ])
    with patch("api.services.podcast_service.requests.get", return_value=response) as mock_get:
        results = search_itunes_podcasts("easy polish", language="pl")

    assert len(results) == 1
    assert results[0] == {
        "title": "Easy Polish",
        "artist": "Easy Languages",
        "image_url": "https://example.com/cover.jpg",
        "rss_url": "https://example.com/feed.xml",
    }
    # Verify country=PL was passed
    called_params = mock_get.call_args.kwargs["params"]
    assert called_params["country"] == "PL"
    assert called_params["term"] == "easy polish"
    assert called_params["media"] == "podcast"


def test_search_itunes_podcasts_omits_country_for_unknown_language():
    """If the language isn't in the country map, no country param is sent."""
    response = _make_itunes_response([])
    with patch("api.services.podcast_service.requests.get", return_value=response) as mock_get:
        search_itunes_podcasts("anything", language="xyz")

    called_params = mock_get.call_args.kwargs["params"]
    assert "country" not in called_params


def test_search_itunes_podcasts_skips_entries_without_feedurl():
    """Entries without a feedUrl can't be added to a user, so drop them."""
    response = _make_itunes_response([
        {"collectionName": "No Feed", "artistName": "X"},  # no feedUrl
        {
            "collectionName": "Has Feed",
            "artistName": "Y",
            "feedUrl": "https://example.com/feed.xml",
            "artworkUrl600": "https://example.com/cover.jpg",
        },
    ])
    with patch("api.services.podcast_service.requests.get", return_value=response):
        results = search_itunes_podcasts("test", language="en")

    assert len(results) == 1
    assert results[0]["title"] == "Has Feed"


def test_search_itunes_podcasts_falls_back_to_artworkurl100():
    """If artworkUrl600 is missing, use artworkUrl100 instead of empty string."""
    response = _make_itunes_response([
        {
            "collectionName": "Small Art",
            "artistName": "X",
            "feedUrl": "https://example.com/feed.xml",
            "artworkUrl100": "https://example.com/small.jpg",
        }
    ])
    with patch("api.services.podcast_service.requests.get", return_value=response):
        results = search_itunes_podcasts("test", language="en")

    assert results[0]["image_url"] == "https://example.com/small.jpg"


def test_search_itunes_podcasts_raises_on_network_error():
    """Network failures must propagate so the route can return 503,
    distinguishing 'iTunes broken' from 'iTunes returned empty'."""
    with patch("api.services.podcast_service.requests.get",
               side_effect=requests.RequestException("connection refused")):
        with pytest.raises(requests.RequestException):
            search_itunes_podcasts("test", language="en")
