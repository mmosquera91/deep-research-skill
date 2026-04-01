"""Tests for ResearchOrchestrator."""

import pytest
import sys
import os
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.research import ResearchOrchestrator
from scripts.storage import ResearchStore, ResearchFinding


class TestResearchOrchestrator:
    """Test suite for ResearchOrchestrator."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        os.unlink(db_path)
    
    @pytest.fixture
    def orchestrator(self, temp_db):
        """Create a ResearchOrchestrator with temp database."""
        return ResearchOrchestrator(db_path=temp_db)
    
    def test_research_generates_plan_with_all_sources(self, orchestrator):
        """Test that research() generates a plan with all default sources."""
        result = orchestrator.research("AI tools")
        
        assert result["topic"] == "AI tools"
        assert result["days"] == 30
        assert len(result["searches"]) == 3
        
        sources = [s["source"] for s in result["searches"]]
        assert "web" in sources
        assert "reddit" in sources
        assert "youtube" in sources
    
    def test_research_generates_queries_with_date_filter(self, orchestrator):
        """Test that queries include date filters for recency."""
        result = orchestrator.research("AI tools", days=7)
        
        since_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        for search in result["searches"]:
            if search["source"] == "web":
                assert "after:" in search["query"]
                assert since_date in search["query"]
            elif search["source"] == "reddit":
                assert "site:reddit.com" in search["query"]
                assert "after:" in search["query"]
            elif search["source"] == "youtube":
                assert "site:youtube.com" in search["query"]
                assert "after:" in search["query"]
    
    def test_research_respects_source_filter(self, orchestrator):
        """Test that research() respects the sources parameter."""
        result = orchestrator.research("AI tools", sources=["reddit"])
        
        assert len(result["searches"]) == 1
        assert result["searches"][0]["source"] == "reddit"
    
    def test_ingest_results_saves_findings(self, orchestrator):
        """Test that ingest_results() saves findings to database."""
        web_results = [
            {
                "url": "https://example.com/article1",
                "title": "Test Article 1",
                "description": "This is a test article about AI"
            },
            {
                "url": "https://example.com/article2",
                "title": "Test Article 2",
                "description": "Another test article"
            }
        ]
        
        count = orchestrator.ingest_results("AI tools", "web", web_results)
        
        assert count == 2
        
        # Verify findings are in database
        findings = orchestrator.get_findings("AI tools")
        assert len(findings) == 2
        
        urls = [f.url for f in findings]
        assert "https://example.com/article1" in urls
        assert "https://example.com/article2" in urls
    
    def test_ingest_results_deduplicates_by_url(self, orchestrator):
        """Test that ingest_results() deduplicates by URL."""
        web_results = [
            {
                "url": "https://example.com/article1",
                "title": "Test Article 1",
                "description": "First occurrence"
            }
        ]
        
        # First ingestion
        count1 = orchestrator.ingest_results("AI tools", "web", web_results)
        assert count1 == 1
        
        # Second ingestion of same URL
        count2 = orchestrator.ingest_results("AI tools", "web", web_results)
        assert count2 == 0  # Should not save duplicate
        
        # Verify only one finding in database
        findings = orchestrator.get_findings("AI tools")
        assert len(findings) == 1
    
    def test_ingest_results_reddit_parsing(self, orchestrator):
        """Test that Reddit results are parsed correctly with scores."""
        reddit_results = [
            {
                "url": "https://reddit.com/r/ai/comments/123",
                "title": "150 votes: Great AI tool discussion",
                "description": "Discussion about AI tools"
            },
            {
                "url": "https://reddit.com/r/ai/comments/456",
                "title": "No votes: Random post",
                "description": "Another discussion"
            }
        ]
        
        count = orchestrator.ingest_results("AI tools", "reddit", reddit_results)
        assert count == 2
        
        findings = orchestrator.get_findings("AI tools")
        
        # Check that score was extracted
        scored = [f for f in findings if f.score is not None]
        assert len(scored) == 1
        assert scored[0].score == 150
    
    def test_ingest_results_youtube_filtering(self, orchestrator):
        """Test that YouTube results are filtered to YouTube URLs only."""
        youtube_results = [
            {
                "url": "https://youtube.com/watch?v=abc123",
                "title": "AI Tutorial",
                "description": "Learn AI"
            },
            {
                "url": "https://vimeo.com/video123",  # Not YouTube
                "title": "AI Video",
                "description": "Learn AI"
            },
            {
                "url": "https://youtu.be/xyz789",  # Short URL
                "title": "AI Explained",
                "description": "AI explained"
            }
        ]
        
        count = orchestrator.ingest_results("AI tools", "youtube", youtube_results)
        assert count == 2  # Only YouTube URLs
        
        findings = orchestrator.get_findings("AI tools")
        urls = [f.url for f in findings]
        assert "https://youtube.com/watch?v=abc123" in urls
        assert "https://youtu.be/xyz789" in urls
        assert "https://vimeo.com/video123" not in urls
    
    def test_get_findings_with_date_filter(self, orchestrator):
        """Test that get_findings respects days parameter."""
        # Add some test findings directly
        store = orchestrator.store
        
        # Old finding (60 days ago)
        old_finding = ResearchFinding(
            topic="AI tools",
            source="web",
            url="https://example.com/old",
            title="Old Article",
            content="Old content",
            published_at=(datetime.now() - timedelta(days=60)).isoformat()
        )
        store.save_finding(old_finding)
        
        # Recent finding (5 days ago)
        recent_finding = ResearchFinding(
            topic="AI tools",
            source="web",
            url="https://example.com/recent",
            title="Recent Article",
            content="Recent content",
            published_at=(datetime.now() - timedelta(days=5)).isoformat()
        )
        store.save_finding(recent_finding)
        
        # Get findings with 30-day filter
        findings = orchestrator.get_findings("AI tools", days=30)
        
        # Should only return recent finding
        assert len(findings) == 1
        assert findings[0].url == "https://example.com/recent"
    
    def test_research_includes_instruction(self, orchestrator):
        """Test that research plan includes instruction for agent."""
        result = orchestrator.research("AI tools")
        
        assert "instruction" in result
        assert "web_search" in result["instruction"]
        assert "ingest_results" in result["instruction"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
