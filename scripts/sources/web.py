from .base import BaseSource, SourceResult
from typing import List
from datetime import datetime, timedelta

class WebSource(BaseSource):
    """General web search via SearXNG/Hermes web_search."""
    
    name = "web"
    
    def search(self, query: str, days: int = 30, limit: int = 10) -> List[SourceResult]:
        """Returns search query for Hermes to execute."""
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return []
    
    def parse_web_search_result(self, result: dict) -> SourceResult:
        """Convert Hermes web_search result to SourceResult."""
        return SourceResult(
            url=result.get("url", ""),
            title=result.get("title", ""),
            content=result.get("description", ""),
            published_at=None,
            score=None,
            source_name=self.name
        )