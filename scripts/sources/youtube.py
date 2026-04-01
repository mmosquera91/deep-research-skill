from .base import BaseSource, SourceResult
from typing import List

class YouTubeSource(BaseSource):
    """YouTube search and transcript extraction."""
    
    name = "youtube"
    
    def _build_query(self, query: str) -> str:
        """Build YouTube search query."""
        return f"{query} site:youtube.com"
    
    def search(self, query: str, days: int = 30, limit: int = 10) -> List[SourceResult]:
        """Returns search parameters for orchestrator."""
        return []
    
    def parse_search_results(self, web_results: List[dict]) -> List[SourceResult]:
        """Parse YouTube search results."""
        results = []
        for item in web_results:
            url = item.get("url", "")
            if "youtube.com" in url or "youtu.be" in url:
                results.append(SourceResult(
                    url=url,
                    title=item.get("title", ""),
                    content=item.get("description", ""),
                    published_at=None,
                    source_name=self.name
                ))
        return results
    
    def format_transcript(self, video_url: str, transcript: str, title: str) -> SourceResult:
        """Format transcript result as SourceResult."""
        return SourceResult(
            url=video_url,
            title=title,
            content=transcript[:3000],
            source_name=self.name,
            metadata={"is_transcript": True}
        )
