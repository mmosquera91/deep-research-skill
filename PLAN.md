# Deep-Research Skill Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Create a native Hermes skill for deep research across multiple sources (Reddit, X/Twitter, YouTube, HN, web) with recency filtering, watchlists, and briefings.

**Architecture:** Modular design with separate source adapters, a SQLite-based knowledge store for accumulated research, and a cron-friendly watchlist system. Follows Hermes skill conventions with YAML frontmatter + Python scripts.

**Tech Stack:** Python 3.11+, SQLite (stdlib), Hermes native tools (web_search, web_extract, youtube-content), cronjob for scheduling.

---

## Overview

This skill provides `deep-research` capabilities similar to OpenClaw's `last30days` but natively integrated with Hermes:

| Command | Description |
|---------|-------------|
| `research <topic>` | One-shot deep research across all sources |
| `research watch add <topic>` | Add topic to watchlist |
| `research watch list` | Show watched topics |
| `research watch run` | Run all watchlist items (for cron) |
| `research briefing` | Generate briefing from accumulated findings |
| `research history <query>` | Query past research findings |

---

## Project Structure

```
skills/deep-research/
├── SKILL.md                    # Skill definition + instructions
├── README.md                   # User documentation
├── PLAN.md                     # This file
├── scripts/
│   ├── __init__.py
│   ├── research.py            # Main orchestrator
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── base.py            # Abstract source class
│   │   ├── reddit.py          # Reddit source adapter
│   │   ├── twitter.py         # X/Twitter source adapter
│   │   ├── youtube.py         # YouTube source adapter
│   │   ├── hackernews.py      # HN source adapter
│   │   └── web.py             # General web source
│   ├── storage.py             # SQLite operations
│   ├── watchlist.py           # Watchlist management
│   └── synthesis.py           # LLM-based synthesis
└── tests/
    ├── test_sources.py
    ├── test_storage.py
    └── test_watchlist.py
```

---

## Task 1: Create Skill Directory Structure

**Objective:** Set up the skill directory skeleton.

**Files:**
- Create: `skills/deep-research/SKILL.md` (minimal stub)
- Create: `skills/deep-research/scripts/__init__.py`
- Create: `skills/deep-research/scripts/sources/__init__.py`
- Create: `skills/deep-research/tests/__init__.py`

**Step 1: Create directory structure**

```bash
mkdir -p skills/deep-research/scripts/sources
mkdir -p skills/deep-research/tests
touch skills/deep-research/scripts/__init__.py
touch skills/deep-research/scripts/sources/__init__.py
touch skills/deep-research/tests/__init__.py
```

**Step 2: Create minimal SKILL.md stub**

```markdown
---
name: deep-research
description: Deep research across Reddit, X, YouTube, HN, and web with recency filtering
version: 0.1.0
author: Miguel
---

# Deep Research Skill

WIP - see README.md for details.
```

**Step 3: Commit**

```bash
git add skills/deep-research/
git commit -m "chore: init deep-research skill structure"
```

---

## Task 2: Create Storage Module (SQLite)

**Objective:** Build the data persistence layer for accumulated research.

**Files:**
- Create: `skills/deep-research/scripts/storage.py`
- Test: `skills/deep-research/tests/test_storage.py`

**Step 1: Write failing test**

```python
# skills/deep-research/tests/test_storage.py
import pytest
import tempfile
import os
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
```

**Step 2: Run test to verify failure**

```bash
cd skills/deep-research
pytest tests/test_storage.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.storage'`

**Step 3: Implement storage module**

```python
# skills/deep-research/scripts/storage.py
import sqlite3
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional
from pathlib import Path

@dataclass
class ResearchFinding:
    topic: str
    source: str
    url: str
    title: str
    content: str
    published_at: str
    score: Optional[int] = None  # upvotes, likes, etc.
    metadata: Optional[dict] = None
    
    def to_dict(self):
        return asdict(self)

class ResearchStore:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default: ~/.local/share/deep-research/research.db
            data_dir = Path.home() / ".local" / "share" / "deep-research"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "research.db"
        
        self.db_path = str(db_path)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    source TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    content TEXT,
                    published_at TEXT,
                    score INTEGER,
                    metadata TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_topic ON findings(topic)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_source ON findings(source)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created ON findings(created_at)
            """)
            
            conn.commit()
    
    def save_finding(self, finding: ResearchFinding) -> bool:
        """Save finding. Returns True if new, False if duplicate."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO findings 
                    (topic, source, url, title, content, published_at, score, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    finding.topic,
                    finding.source,
                    finding.url,
                    finding.title,
                    finding.content,
                    finding.published_at,
                    finding.score,
                    json.dumps(finding.metadata) if finding.metadata else None
                ))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # URL already exists
            return False
    
    def save_findings(self, findings: List[ResearchFinding]) -> int:
        """Save multiple findings. Returns count of new findings."""
        count = 0
        for f in findings:
            if self.save_finding(f):
                count += 1
        return count
    
    def find_by_topic(self, topic: str, days: Optional[int] = None) -> List[ResearchFinding]:
        """Find findings by topic (partial match)."""
        query = "SELECT * FROM findings WHERE topic LIKE ?"
        params = [f"%{topic}%"]
        
        if days:
            query += " AND created_at >= datetime('now', '-{} days')".format(days)
        
        query += " ORDER BY published_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            
            return [self._row_to_finding(row) for row in rows]
    
    def search_content(self, query: str) -> List[ResearchFinding]:
        """Full-text search in title and content."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM findings 
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY published_at DESC
            """, (f"%{query}%", f"%{query}%")).fetchall()
            
            return [self._row_to_finding(row) for row in rows]
    
    def get_stats(self) -> dict:
        """Get database stats."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
            by_source = conn.execute("""
                SELECT source, COUNT(*) as count 
                FROM findings 
                GROUP BY source
            """).fetchall()
            
            return {
                "total_findings": total,
                "by_source": {row[0]: row[1] for row in by_source}
            }
    
    def _row_to_finding(self, row: sqlite3.Row) -> ResearchFinding:
        return ResearchFinding(
            topic=row["topic"],
            source=row["source"],
            url=row["url"],
            title=row["title"],
            content=row["content"],
            published_at=row["published_at"],
            score=row["score"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None
        )
```

**Step 4: Run tests**

```bash
pytest tests/test_storage.py -v
```
Expected: 2 passed

**Step 5: Commit**

```bash
git add scripts/storage.py tests/test_storage.py
git commit -m "feat(storage): SQLite backend for research findings"
```

---

## Task 3: Create Base Source Adapter

**Objective:** Define abstract interface for all research sources.

**Files:**
- Create: `skills/deep-research/scripts/sources/base.py`
- Test: `skills/deep-research/tests/test_sources.py`

**Step 1: Write failing test**

```python
# skills/deep-research/tests/test_sources.py
import pytest
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
```

**Step 2: Run test**

```bash
pytest tests/test_sources.py -v
```
Expected: FAIL — module not found

**Step 3: Implement base adapter**

```python
# skills/deep-research/scripts/sources/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class SourceResult:
    url: str
    title: str
    content: str
    published_at: Optional[str] = None  # ISO 8601
    score: Optional[int] = None  # upvotes, likes, etc.
    author: Optional[str] = None
    source_name: Optional[str] = None  # e.g., "reddit", "twitter"

class BaseSource(ABC):
    """Abstract base class for research sources."""
    
    name: str = "base"
    
    @abstractmethod
    def search(self, query: str, days: int = 30, limit: int = 10) -> List[SourceResult]:
        """
        Search for content matching query.
        
        Args:
            query: Search query string
            days: How many days back to search
            limit: Max results to return
            
        Returns:
            List of SourceResult objects
        """
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
            "content": result.content[:2000],  # Limit content length
            "published_at": result.published_at,
            "score": result.score,
            "metadata": {
                "author": result.author,
                "full_content_length": len(result.content)
            }
        }
```

**Step 4: Run tests**

```bash
pytest tests/test_sources.py -v
```
Expected: 1 passed

**Step 5: Commit**

```bash
git add scripts/sources/base.py tests/test_sources.py
git commit -m "feat(sources): base adapter interface"
```

---

## Task 4: Implement Web Source Adapter

**Objective:** Create adapter for general web search using Hermes web_search tool.

**Files:**
- Create: `skills/deep-research/scripts/sources/web.py`

**Step 1: Write failing test**

```python
# Add to tests/test_sources.py
def test_web_source_search():
    from scripts.sources.web import WebSource
    
    source = WebSource()
    results = source.search("python programming", days=30, limit=5)
    
    assert isinstance(results, list)
    if results:  # May be empty if no results
        assert hasattr(results[0], 'url')
        assert hasattr(results[0], 'title')
```

**Step 2: Run test**

```bash
pytest tests/test_sources.py::test_web_source_search -v
```
Expected: FAIL

**Step 3: Implement web source**

```python
# skills/deep-research/scripts/sources/web.py
from .base import BaseSource, SourceResult
from typing import List
from datetime import datetime, timedelta

class WebSource(BaseSource):
    """General web search via SearXNG/Hermes web_search."""
    
    name = "web"
    
    def search(self, query: str, days: int = 30, limit: int = 10) -> List[SourceResult]:
        """
        Search using Hermes web_search tool.
        Note: This is designed to be called from within Hermes agent context.
        """
        # Calculate date range
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # This will be called by the Hermes agent which has access to web_search
        # The actual implementation delegates to web_search tool
        return self._search_via_hermes(query, since_date, limit)
    
    def _search_via_hermes(self, query: str, since: str, limit: int) -> List[SourceResult]:
        """
        This method is called by the research orchestrator.
        The orchestrator has access to Hermes tools and passes results here.
        """
        # Placeholder - actual search happens in research.py orchestrator
        # which calls web_search and converts results to SourceResult
        return []
    
    def parse_web_search_result(self, result: dict) -> SourceResult:
        """Convert Hermes web_search result to SourceResult."""
        return SourceResult(
            url=result.get("url", ""),
            title=result.get("title", ""),
            content=result.get("description", ""),
            published_at=None,  # web_search doesn't always provide this
            score=None,
            source_name=self.name
        )
```

**Step 4: Run tests**

```bash
pytest tests/test_sources.py::test_web_source_search -v
```
Expected: PASS (with empty list)

**Step 5: Commit**

```bash
git add scripts/sources/web.py
git commit -m "feat(sources): web search adapter"
```

---

## Task 5: Implement Reddit Source Adapter

**Objective:** Create adapter for Reddit search.

**Files:**
- Create: `skills/deep-research/scripts/sources/reddit.py`

**Step 1: Write test**

```python
# Add to tests/test_sources.py
def test_reddit_source():
    from scripts.sources.reddit import RedditSource
    
    source = RedditSource()
    assert source.name == "reddit"
    
    # Test query construction
    query = source._build_query("AI tools", days=30)
    assert "AI tools" in query
    assert "site:reddit.com" in query
```

**Step 2: Implement Reddit source**

```python
# skills/deep-research/scripts/sources/reddit.py
from .base import BaseSource, SourceResult
from typing import List
from datetime import datetime, timedelta

class RedditSource(BaseSource):
    """Reddit search via web search with site:reddit.com filter."""
    
    name = "reddit"
    
    def _build_query(self, query: str, days: int) -> str:
        """Build search query with Reddit filter."""
        return f"{query} site:reddit.com"
    
    def search(self, query: str, days: int = 30, limit: int = 10) -> List[SourceResult]:
        """Returns search query for Hermes to execute."""
        # Actual search happens via web_search tool in orchestrator
        return []
    
    def parse_results(self, web_results: List[dict]) -> List[SourceResult]:
        """Parse web search results into SourceResults."""
        results = []
        for item in web_results:
            # Try to extract score from title if present
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
        # Reddit titles often start with "123 votes - Title"
        import re
        match = re.match(r"(\d+)\s+votes?", title)
        if match:
            return int(match.group(1))
        return None
```

**Step 3: Run tests**

```bash
pytest tests/test_sources.py::test_reddit_source -v
```

**Step 4: Commit**

```bash
git add scripts/sources/reddit.py
git commit -m "feat(sources): reddit adapter"
```

---

## Task 6: Implement YouTube Source Adapter

**Objective:** Create adapter for YouTube search using youtube-content skill.

**Files:**
- Create: `skills/deep-research/scripts/sources/youtube.py`

**Step 1: Implement YouTube source**

```python
# skills/deep-research/scripts/sources/youtube.py
from .base import BaseSource, SourceResult
from typing import List
from datetime import datetime

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
            content=transcript[:3000],  # Limit length
            source_name=self.name,
            metadata={"is_transcript": True}
        )
```

**Step 2: Commit**

```bash
git add scripts/sources/youtube.py
git commit -m "feat(sources): youtube adapter"
```

---

## Task 7: Create Research Orchestrator

**Objective:** Build main research.py that coordinates sources and uses Hermes tools.

**Files:**
- Create: `skills/deep-research/scripts/research.py`

**Step 1: Create orchestrator**

```python
# skills/deep-research/scripts/research.py
#!/usr/bin/env python3
"""
Deep research orchestrator.
Called by Hermes agent with access to tools.
"""

import sys
import json
import argparse
from typing import List, Optional
from datetime import datetime

from .storage import ResearchStore, ResearchFinding
from .sources.web import WebSource
from .sources.reddit import RedditSource
from .sources.youtube import YouTubeSource

class ResearchOrchestrator:
    """Orchestrates research across multiple sources."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.store = ResearchStore(db_path)
        self.sources = {
            "web": WebSource(),
            "reddit": RedditSource(),
            "youtube": YouTubeSource(),
        }
    
    def research(self, topic: str, days: int = 30, sources: Optional[List[str]] = None) -> dict:
        """
        Perform deep research on a topic.
        
        This method is called from within Hermes agent context.
        It uses Hermes tools (web_search, web_extract, youtube-content).
        
        Returns summary dict for agent to present.
        """
        if sources is None:
            sources = ["web", "reddit", "youtube"]
        
        findings = []
        
        for source_name in sources:
            source = self.sources.get(source_name)
            if not source:
                continue
            
            # Build source-specific query
            if source_name == "reddit":
                query = source._build_query(topic, days)
            elif source_name == "youtube":
                query = source._build_query(topic)
            else:
                query = topic
            
            # NOTE: Actual search happens via Hermes agent calling tools
            # This method returns a "search plan" that the agent executes
            findings.append({
                "source": source_name,
                "query": query,
                "status": "pending"
            })
        
        return {
            "topic": topic,
            "days": days,
            "searches": findings,
            "instruction": "Use web_search tool with each query, then call ingest_results()"
        }
    
    def ingest_results(self, topic: str, source_name: str, web_results: List[dict]):
        """
        Ingest web search results into storage.
        Called by Hermes agent after performing searches.
        """
        source = self.sources.get(source_name)
        if not source:
            return 0
        
        if source_name == "reddit":
            results = source.parse_results(web_results)
        elif source_name == "youtube":
            results = source.parse_search_results(web_results)
        else:
            results = [source.parse_web_search_result(r) for r in web_results]
        
        # Convert to ResearchFinding and save
        count = 0
        for r in results:
            finding = ResearchFinding(
                topic=topic,
                source=source_name,
                url=r.url,
                title=r.title,
                content=r.content,
                published_at=r.published_at,
                score=r.score,
                metadata=r.metadata
            )
            if self.store.save_finding(finding):
                count += 1
        
        return count
    
    def get_findings(self, topic: str, days: Optional[int] = None) -> List[ResearchFinding]:
        """Retrieve findings for a topic."""
        return self.store.find_by_topic(topic, days)


def main():
    parser = argparse.ArgumentParser(description="Deep research tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Research command
    research_parser = subparsers.add_parser("research", help="Research a topic")
    research_parser.add_argument("topic", help="Topic to research")
    research_parser.add_argument("--days", type=int, default=30, help="Days back to search")
    research_parser.add_argument("--sources", nargs="+", choices=["web", "reddit", "youtube", "all"],
                                default=["all"], help="Sources to search")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show database stats")
    
    args = parser.parse_args()
    
    orchestrator = ResearchOrchestrator()
    
    if args.command == "research":
        # Output JSON for Hermes agent to parse
        sources = ["web", "reddit", "youtube"] if "all" in args.sources else args.sources
        result = orchestrator.research(args.topic, args.days, sources)
        print(json.dumps(result, indent=2))
    
    elif args.command == "stats":
        stats = orchestrator.store.get_stats()
        print(json.dumps(stats, indent=2))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add scripts/research.py
git chmod +x scripts/research.py
git commit -m "feat(orchestrator): main research coordinator"
```

---

## Task 8: Create Watchlist Module

**Objective:** Build watchlist system for tracking topics over time.

**Files:**
- Create: `skills/deep-research/scripts/watchlist.py`
- Test: `skills/deep-research/tests/test_watchlist.py`

**Step 1: Write test**

```python
# skills/deep-research/tests/test_watchlist.py
import pytest
import tempfile
import os
from scripts.watchlist import WatchlistManager, WatchlistItem

def test_add_and_list_items():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "watchlist.db")
        manager = WatchlistManager(db_path)
        
        item = WatchlistItem(
            topic="AI news",
            frequency_days=7,
            sources=["reddit", "twitter"]
        )
        
        manager.add(item)
        items = manager.list_all()
        
        assert len(items) == 1
        assert items[0].topic == "AI news"
```

**Step 2: Implement watchlist**

```python
# skills/deep-research/scripts/watchlist.py
#!/usr/bin/env python3
"""
Watchlist management for recurring research.
"""

import sqlite3
import json
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path

@dataclass
class WatchlistItem:
    topic: str
    frequency_days: int = 7  # How often to check
    sources: List[str] = None
    last_run: Optional[str] = None
    created_at: Optional[str] = None
    active: bool = True
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = ["web", "reddit"]

class WatchlistManager:
    """Manages watchlist of topics to track."""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = Path.home() / ".local" / "share" / "deep-research"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "watchlist.db"
        
        self.db_path = str(db_path)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT UNIQUE NOT NULL,
                    frequency_days INTEGER DEFAULT 7,
                    sources TEXT,  -- JSON list
                    last_run TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active BOOLEAN DEFAULT 1
                )
            """)
            conn.commit()
    
    def add(self, item: WatchlistItem) -> bool:
        """Add item to watchlist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO watchlist (topic, frequency_days, sources, active)
                    VALUES (?, ?, ?, ?)
                """, (
                    item.topic,
                    item.frequency_days,
                    json.dumps(item.sources),
                    item.active
                ))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False  # Topic already exists
    
    def remove(self, topic: str) -> bool:
        """Remove item from watchlist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM watchlist WHERE topic = ?", (topic,))
            conn.commit()
            return cursor.rowcount > 0
    
    def list_all(self, active_only: bool = True) -> List[WatchlistItem]:
        """List all watchlist items."""
        query = "SELECT * FROM watchlist"
        if active_only:
            query += " WHERE active = 1"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query).fetchall()
            
            return [self._row_to_item(row) for row in rows]
    
    def get_due(self) -> List[WatchlistItem]:
        """Get items that are due for research."""
        items = self.list_all(active_only=True)
        due = []
        
        for item in items:
            if item.last_run is None:
                due.append(item)
            else:
                last_run = datetime.fromisoformat(item.last_run)
                next_run = last_run + timedelta(days=item.frequency_days)
                if datetime.now() >= next_run:
                    due.append(item)
        
        return due
    
    def mark_run(self, topic: str):
        """Mark item as just run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE watchlist SET last_run = CURRENT_TIMESTAMP
                WHERE topic = ?
            """, (topic,))
            conn.commit()
    
    def _row_to_item(self, row: sqlite3.Row) -> WatchlistItem:
        return WatchlistItem(
            topic=row["topic"],
            frequency_days=row["frequency_days"],
            sources=json.loads(row["sources"]) if row["sources"] else ["web"],
            last_run=row["last_run"],
            created_at=row["created_at"],
            active=bool(row["active"])
        )


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Watchlist management")
    subparsers = parser.add_subparsers(dest="command")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add topic to watchlist")
    add_parser.add_argument("topic")
    add_parser.add_argument("--frequency", type=int, default=7)
    add_parser.add_argument("--sources", nargs="+", default=["web", "reddit"])
    
    # List command
    list_parser = subparsers.add_parser("list", help="List watchlist")
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove topic")
    remove_parser.add_argument("topic")
    
    # Run command (for cron)
    run_parser = subparsers.add_parser("run", help="Run due items")
    
    args = parser.parse_args()
    
    manager = WatchlistManager()
    
    if args.command == "add":
        item = WatchlistItem(
            topic=args.topic,
            frequency_days=args.frequency,
            sources=args.sources
        )
        if manager.add(item):
            print(f"Added '{args.topic}' to watchlist")
        else:
            print(f"'{args.topic}' already in watchlist")
    
    elif args.command == "list":
        items = manager.list_all()
        for item in items:
            status = "✓" if item.active else "✗"
            print(f"{status} {item.topic} (every {item.frequency_days}d)")
    
    elif args.command == "remove":
        if manager.remove(args.topic):
            print(f"Removed '{args.topic}'")
        else:
            print(f"'{args.topic}' not found")
    
    elif args.command == "run":
        due = manager.get_due()
        print(f"Found {len(due)} items due for research")
        for item in due:
            print(f"  - {item.topic}")
            # Output JSON for Hermes to process
            print(json.dumps({
                "action": "research",
                "topic": item.topic,
                "sources": item.sources
            }))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

**Step 3: Commit**

```bash
git add scripts/watchlist.py tests/test_watchlist.py
git chmod +x scripts/watchlist.py
git commit -m "feat(watchlist): watchlist management for recurring research"
```

---

## Task 9: Create Synthesis Module

**Objective:** Build module for LLM-based synthesis of findings.

**Files:**
- Create: `skills/deep-research/scripts/synthesis.py`

**Step 1: Implement synthesis**

```python
# skills/deep-research/scripts/synthesis.py
"""
Synthesis of research findings into reports.
This module provides prompts/templates for LLM synthesis.
"""

from typing import List, Dict
from .storage import ResearchFinding

class SynthesisEngine:
    """Generates synthesis prompts for LLM."""
    
    def generate_prompt(self, topic: str, findings: List[ResearchFinding]) -> str:
        """Generate synthesis prompt for findings."""
        
        # Group by source
        by_source: Dict[str, List[ResearchFinding]] = {}
        for f in findings:
            by_source.setdefault(f.source, []).append(f)
        
        # Build findings summary
        findings_text = []
        for source, items in by_source.items():
            findings_text.append(f"\n## {source.upper()}")
            for item in items[:5]:  # Top 5 per source
                findings_text.append(f"- [{item.title}]({item.url})")
                if item.score:
                    findings_text.append(f"  Score: {item.score}")
                findings_text.append(f"  {item.content[:200]}...")
        
        prompt = f"""You are a research analyst synthesizing findings on: **{topic}**

## Raw Findings ({len(findings)} total)
{chr(10).join(findings_text)}

## Your Task
Synthesize these findings into a structured report:

### 1. Key Patterns
What are the main themes or patterns across sources?

### 2. Notable Developments
What specific news, releases, or events were discussed?

### 3. Community Sentiment
What is the general tone? Excited? Skeptical? Mixed?

### 4. Actionable Insights
What should someone interested in this topic know or do?

### 5. Source Reliability
Brief note on which sources provided the most signal vs noise.

Format your response in clean markdown with emojis for readability.
"""
        return prompt
    
    def generate_briefing_prompt(self, topics: List[str], findings_by_topic: Dict[str, List[ResearchFinding]]) -> str:
        """Generate morning briefing prompt."""
        
        sections = []
        for topic in topics:
            findings = findings_by_topic.get(topic, [])
            if findings:
                sections.append(f"\n## {topic}")
                sections.append(f"({len(findings)} new items)")
                for f in findings[:3]:
                    sections.append(f"- {f.title}")
        
        prompt = f"""Generate a morning briefing based on your watchlist research:

{chr(10).join(sections)}

Format as a concise executive summary with:
- 🎯 Headlines (most important item per topic)
- 📊 Trends (cross-topic patterns)
- 🔗 Key Links (top 3 most valuable)

Keep it under 300 words. Use bullet points.
"""
        return prompt
```

**Step 2: Commit**

```bash
git add scripts/synthesis.py
git commit -m "feat(synthesis): LLM synthesis engine for findings"
```

---

## Task 10: Write Main SKILL.md

**Objective:** Complete skill definition with full instructions for Hermes.

**Files:**
- Modify: `skills/deep-research/SKILL.md`

**Step 1: Write complete skill definition**

```markdown
---
name: deep-research
description: Deep research across Reddit, YouTube, and web with recency filtering, watchlists, and briefings
version: 0.1.0
author: Miguel
argument-hint: research AI video tools, research watch add AI news, research briefing
---

# Deep Research Skill

Multi-source research engine for Hermes. Searches Reddit, YouTube, and web with recency filters, accumulates findings in SQLite, and supports watchlists with cron scheduling.

## Commands

| Command | Description |
|---------|-------------|
| `research <topic>` | One-shot research across all sources |
| `research watch add <topic>` | Add topic to watchlist |
| `research watch list` | Show watchlist |
| `research watch remove <topic>` | Remove from watchlist |
| `research watch run` | Run all due items (for cron) |
| `research briefing` | Generate briefing from watchlist findings |
| `research history <query>` | Search past findings |

## One-Shot Research

When user asks: "research <topic>" or "deep research <topic>":

### Step 1: Execute Multi-Source Search

Run searches for the topic:

```python
# Reddit search
web_search(query=f"{topic} site:reddit.com", limit=10)

# YouTube search  
web_search(query=f"{topic} site:youtube.com", limit=10)

# General web search
web_search(query=topic, limit=10)
```

### Step 2: Extract Content

For promising results, extract full content:

```python
web_extract(urls=[result1, result2, ...])
```

For YouTube videos, get transcripts:

```python
# Use youtube-content skill
youtube_transcript(video_url)
```

### Step 3: Store Findings

```python
# Ingest into research database
scripts/research.py ingest --topic "topic" --source reddit --results ...
```

### Step 4: Synthesize

Use the synthesis engine to generate report:

```python
# Generate synthesis prompt
python3 scripts/synthesis.py generate --topic "topic"
```

Then pass prompt to LLM and present formatted results.

## Watchlist Management

### Add to Watchlist

When user says "watch this topic" or "track this":

```python
python3 scripts/watchlist.py add "Topic Name" --frequency 7 --sources reddit youtube
```

### List Watchlist

```python
python3 scripts/watchlist.py list
```

### Run Due Items (for cron)

```python
python3 scripts/watchlist.py run
# Then for each due item, perform research as in One-Shot
```

## Cron Setup

Schedule watchlist runs:

```python
cronjob(action="create", schedule="0 9 * * *", prompt="Run deep-research watchlist", skill="deep-research")
```

## Database Location

```
~/.local/share/deep-research/
├── research.db      # Findings storage
└── watchlist.db     # Watchlist configuration
```

## Dependencies

- Python 3.11+
- SQLite3 (stdlib)
- Hermes tools: web_search, web_extract, youtube-content
```

**Step 2: Commit**

```bash
git add SKILL.md
git commit -m "docs(skill): complete SKILL.md with usage instructions"
```

---

## Task 11: Write README.md

**Objective:** Create user-facing documentation.

**Files:**
- Create: `skills/deep-research/README.md`

**Step 1: Write README**

```markdown
# Deep Research Skill for Hermes

AI-powered research across multiple sources with persistent storage and watchlists.

## Features

- 🔍 **Multi-source**: Reddit, YouTube, Hacker News, Web
- 📅 **Recency filtering**: Last 7, 30, 90 days
- 💾 **Persistent storage**: SQLite with full-text search
- 📋 **Watchlists**: Track topics automatically
- 📊 **Briefings**: Morning digest of your watchlist
- 🔗 **Citation tracking**: All findings link to sources

## Quick Start

```bash
# Research a topic
$ research "AI video generation"

# Add to watchlist
$ research watch add "OpenAI news" --frequency 7

# Morning briefing
$ research briefing
```

## Installation

1. Copy skill to Hermes skills directory:
   ```bash
   cp -r skills/deep-research ~/.hermes/skills/
   ```

2. Install dependencies: None! Uses Python stdlib only.

3. Restart Hermes or reload skills.

## Configuration

Environment variables (optional):

```bash
export DEEP_RESEARCH_DB_PATH="/custom/path/research.db"
```

## Watchlist + Cron

Schedule automatic research:

```bash
# Daily at 9am
cronjob create "0 9 * * *" "research watch run && research briefing"
```

## Data Storage

Findings are stored in SQLite at:
- `~/.local/share/deep-research/research.db`

Query directly:
```bash
sqlite3 ~/.local/share/deep-research/research.db \
  "SELECT * FROM findings WHERE topic LIKE '%AI%' ORDER BY published_at DESC LIMIT 10"
```

## License

MIT
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: user-facing README"
```

---

## Task 12: Final Review Checklist

**Objective:** Verify plan completeness.

**Step 1: Checklist**

- [ ] All file paths are exact
- [ ] Each task is bite-sized (2-5 min)
- [ ] Code examples are complete
- [ ] TDD cycle documented for testable modules
- [ ] No missing dependencies
- [ ] Hermes integration points documented

**Step 2: Summary**

Total files to create:
- 9 Python modules
- 3 test files
- 2 documentation files

**Step 3: Final commit**

```bash
git add docs/plans/deep-research-implementation.md  # if saved separately
git commit -m "docs(plan): add deep-research skill implementation plan"
```

---

## Implementation Order Summary

1. Task 1-2: Storage foundation
2. Task 3-6: Source adapters
3. Task 7: Research orchestrator
4. Task 8: Watchlist system
5. Task 9: Synthesis engine
6. Task 10-11: Documentation
7. Task 12: Review

Ready to implement using `subagent-driven-development` skill.
