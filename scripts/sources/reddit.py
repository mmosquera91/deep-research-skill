from .base import BaseSource, SourceResult
from typing import List, Optional
from datetime import datetime, timedelta
import re

class RedditSource(BaseSource):
    """Reddit search via web search with site:reddit.com filter."""
    
    name = "reddit"
    
    def _build_query(self, query: str, days: int = 30) -> str:
        """Build search query with Reddit filter and date range.
        
        Uses 'after:' operator for recency filtering.
        """
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return f"{query} site:reddit.com after:{since_date}"
    
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
    
    def parse_results(self, web_results: List[dict]) -> List[SourceResult]:
        """Parse web search results into SourceResults."""
        results = []
        for item in web_results:
            title = item.get("title", "")
            score = self._extract_score(title)
            
            results.append(SourceResult(
                url=item.get("url", ""),
                title=title,
                content=item.get("description", ""),
                published_at=None,
                score=score,
                source_name=self.name
            ))
        return results
    
    def _extract_score(self, title: str) -> Optional[int]:
        """Try to extract upvote score from Reddit title."""
        match = re.match(r"(\d+)\s+votes?", title)
        if match:
            return int(match.group(1))
        return None