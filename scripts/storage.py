import sqlite3
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path


def normalize_topic(topic: str) -> str:
    """Normalize topic for consistent grouping.
    
    Examples:
        "AI Coding Tools" → "ai_coding_tools"
        "AI-tools" → "ai_tools"
        "  spaces  " → "spaces"
    """
    # Lowercase
    normalized = topic.lower()
    # Replace hyphens and multiple spaces with underscore
    normalized = re.sub(r'[-\s]+', '_', normalized.strip())
    # Remove non-alphanumeric except underscore
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)
    # Collapse multiple underscores
    normalized = re.sub(r'_+', '_', normalized)
    return normalized.strip('_')

@dataclass
class ResearchFinding:
    topic: str
    source: str
    url: str
    title: str
    content: str
    published_at: str
    score: Optional[int] = None
    metadata: Optional[dict] = None
    
    def to_dict(self):
        return asdict(self)

class ResearchStore:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = Path.home() / ".local" / "share" / "deep-research"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "research.db"
        
        self.db_path = str(db_path)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # Main findings table
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
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Migration: Add normalized_topic column if not exists
            cursor = conn.execute("PRAGMA table_info(findings)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'normalized_topic' not in columns:
                conn.execute("ALTER TABLE findings ADD COLUMN normalized_topic TEXT")
                # Populate normalized_topic for existing rows
                conn.execute("UPDATE findings SET normalized_topic = LOWER(REPLACE(REPLACE(topic, ' ', '_'), '-', '_'))")
                conn.execute("CREATE INDEX idx_normalized_topic ON findings(normalized_topic)")
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_topic ON findings(topic)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON findings(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON findings(created_at)")
            
            # FTS5 virtual table for full-text search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS findings_fts USING fts5(
                    title,
                    content,
                    content='findings',
                    content_rowid='id'
                )
            """)
            
            # Triggers to keep FTS index in sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS findings_ai AFTER INSERT ON findings BEGIN
                    INSERT INTO findings_fts(rowid, title, content)
                    VALUES (new.id, new.title, new.content);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS findings_ad AFTER DELETE ON findings BEGIN
                    INSERT INTO findings_fts(findings_fts, rowid, title, content)
                    VALUES ('delete', old.id, old.title, old.content);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS findings_au AFTER UPDATE ON findings BEGIN
                    INSERT INTO findings_fts(findings_fts, rowid, title, content)
                    VALUES ('delete', old.id, old.title, old.content);
                    INSERT INTO findings_fts(rowid, title, content)
                    VALUES (new.id, new.title, new.content);
                END
            """)
            conn.commit()
    
    def save_finding(self, finding: ResearchFinding) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                normalized = normalize_topic(finding.topic)
                conn.execute("""
                    INSERT INTO findings 
                    (topic, normalized_topic, source, url, title, content, published_at, score, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    finding.topic, normalized, finding.source, finding.url, finding.title,
                    finding.content, finding.published_at, finding.score,
                    json.dumps(finding.metadata) if finding.metadata else None
                ))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def save_findings(self, findings: List[ResearchFinding]) -> int:
        count = 0
        for f in findings:
            if self.save_finding(f):
                count += 1
        return count
    
    def find_by_topic(self, topic: str, days: Optional[int] = None) -> List[ResearchFinding]:
        """Find findings by topic (searches both original and normalized forms)."""
        normalized = normalize_topic(topic)
        
        # Search by normalized_topic for exact matches, or original topic for partial matches
        query = "SELECT * FROM findings WHERE normalized_topic = ? OR topic LIKE ?"
        params = [normalized, f"%{topic}%"]
        query += " ORDER BY published_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            findings = [self._row_to_finding(row) for row in rows]
        
        # Apply days filter in Python to handle ISO date format correctly
        if days and findings:
            cutoff = datetime.now() - timedelta(days=days)
            filtered = []
            for f in findings:
                if f.published_at is None:
                    filtered.append(f)
                    continue
                try:
                    # Parse ISO format
                    parsed = datetime.fromisoformat(f.published_at.replace('Z', '+00:00').replace('+00:00', ''))
                    if parsed >= cutoff:
                        filtered.append(f)
                except (ValueError, TypeError):
                    # If parsing fails, include it
                    filtered.append(f)
            return filtered
        
        return findings
    
    def find_by_normalized_topic(self, normalized_topic: str, days: Optional[int] = None) -> List[ResearchFinding]:
        """Find findings by normalized topic (exact match)."""
        query = "SELECT * FROM findings WHERE normalized_topic = ? ORDER BY published_at DESC"
        params = [normalized_topic]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            findings = [self._row_to_finding(row) for row in rows]
        
        # Apply days filter in Python
        if days and findings:
            cutoff = datetime.now() - timedelta(days=days)
            filtered = []
            for f in findings:
                if f.published_at is None:
                    filtered.append(f)
                    continue
                try:
                    parsed = datetime.fromisoformat(f.published_at.replace('Z', '+00:00').replace('+00:00', ''))
                    if parsed >= cutoff:
                        filtered.append(f)
                except (ValueError, TypeError):
                    filtered.append(f)
            return filtered
        
        return findings
    
    def search_content(self, query: str) -> List[ResearchFinding]:
        """Search content using FTS5 for full-text search.
        
        Falls back to LIKE if query is not valid FTS5 syntax.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Try FTS5 first (supports phrases, AND, OR, NOT)
            try:
                rows = conn.execute("""
                    SELECT f.* FROM findings f
                    JOIN findings_fts fts ON f.id = fts.rowid
                    WHERE findings_fts MATCH ?
                    ORDER BY rank
                """, (query,)).fetchall()
                
                if rows:
                    return [self._row_to_finding(row) for row in rows]
            except sqlite3.OperationalError:
                # FTS query failed, fall back to LIKE
                pass
            
            # Fallback to LIKE search
            rows = conn.execute("""
                SELECT * FROM findings WHERE title LIKE ? OR content LIKE ?
                ORDER BY published_at DESC
            """, (f"%{query}%", f"%{query}%")).fetchall()
            return [self._row_to_finding(row) for row in rows]
    
    def get_stats(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
            by_source = conn.execute("SELECT source, COUNT(*) FROM findings GROUP BY source").fetchall()
            return {"total_findings": total, "by_source": {row[0]: row[1] for row in by_source}}
    
    def _row_to_finding(self, row: sqlite3.Row) -> ResearchFinding:
        return ResearchFinding(
            topic=row["topic"], source=row["source"], url=row["url"],
            title=row["title"], content=row["content"], published_at=row["published_at"],
            score=row["score"], metadata=json.loads(row["metadata"]) if row["metadata"] else None
        )
