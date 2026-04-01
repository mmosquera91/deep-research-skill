import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.sources.base import SourceResult
from datetime import datetime

def test_reddit_source():
    from scripts.sources.reddit import RedditSource
    source = RedditSource()
    assert source.name == "reddit"
    query = source._build_query("AI tools", days=30)
    assert "AI tools" in query
    assert "site:reddit.com" in query

def test_web_source_search():
    from scripts.sources.web import WebSource
    source = WebSource()
    results = source.search("python programming", days=30, limit=5)
    assert isinstance(results, list)
    assert source.name == "web"

def test_source_result_creation():
    result = SourceResult(
        url="https://example.com",
        title="Test",
        content="Content",
        published_at="2026-03-30T10:00:00Z",
        score=100
    )
    assert result.title == "Test"
    assert result.score == 100
    assert result.url == "https://example.com"

def test_youtube_source():
    from scripts.sources.youtube import YouTubeSource
    source = YouTubeSource()
    assert source.name == "youtube"
    query = source._build_query("python tutorial")
    assert "python tutorial" in query
    assert "site:youtube.com" in query
