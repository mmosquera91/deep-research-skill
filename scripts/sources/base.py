from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class SourceResult:
    url: str
    title: str
    content: str
    published_at: Optional[str] = None
    score: Optional[int] = None
    author: Optional[str] = None
    source_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default=None)

class BaseSource(ABC):
    """Abstract base class for research sources."""
    
    name: str = "base"
    
    @abstractmethod
    def search(self, query: str, days: int = 30, limit: int = 10) -> List[SourceResult]:
        """Search for content matching query."""
        pass
    
    def is_available(self) -> bool:
        """Check if this source is properly configured and available."""
        return True
    
    def format_for_storage(self, result: SourceResult, topic: str) -> dict:
        """Convert SourceResult to dict for storage."""
        return {
            "topic": topic,
            "source": self.name,
            "url": result.url,
            "title": result.title,
            "content": result.content[:2000],
            "published_at": result.published_at,
            "score": result.score,
            "metadata": {
                "author": result.author,
                "full_content_length": len(result.content)
            }
        }
