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
            conn.execute("CREATE INDEX IF NOT EXISTS idx_topic ON findings(topic)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON findings(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON findings(created_at)")
            conn.commit()
    
    def save_finding(self, finding: ResearchFinding) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO findings 
                    (topic, source, url, title, content, published_at, score, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    finding.topic, finding.source, finding.url, finding.title,
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
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
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
