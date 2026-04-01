import pytest
import tempfile
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.storage import ResearchStore, ResearchFinding

def test_store_init_creates_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = ResearchStore(db_path)
        assert os.path.exists(db_path)

def test_save_and_retrieve_finding():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = ResearchStore(db_path)
        
        finding = ResearchFinding(
            topic="AI tools",
            source="reddit",
            url="https://reddit.com/r/ai/comments/123",
            title="New AI tool released",
            content="Check out this tool...",
            published_at="2026-03-30T10:00:00Z"
        )
        
        store.save_finding(finding)
        results = store.find_by_topic("AI tools")
        
        assert len(results) == 1
        assert results[0].title == "New AI tool released"
