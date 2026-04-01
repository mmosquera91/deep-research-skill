import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.sources.base import SourceResult
from datetime import datetime

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
