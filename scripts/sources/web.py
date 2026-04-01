from .base import BaseSource, SourceResult
from typing import List
from datetime import datetime, timedelta

class WebSource(BaseSource):
    """General web search via SearXNG/Hermes web_search."""
    
    name = "web"
    
    def _build_query(self, query: str, days: int = 30) -> str:
        """Build search query with date filter.
        
        Uses 'after:' operator supported by Google and most search engines.
        """
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return f"{query} after:{since_date}"
    
    def get_search_params(self, query: str, days: int = 30, limit: int = 10) -> dict:
        """Return search parameters including date-filtered query."""
        return {
            "query": self._build_query(query, days),
            "days": days,
            "limit": limit,
            "source_name": self.name
        }
    
    def search(self, query: str, days: int = 30, limit: int = 10) -> List[SourceResult]:
        """Returns search query for Hermes to execute."""
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