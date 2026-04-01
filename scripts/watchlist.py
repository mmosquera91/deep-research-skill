#!/usr/bin/env python3
"""Watchlist management for recurring research."""

import sqlite3
import json
import argparse
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path

@dataclass
class WatchlistItem:
    topic: str
    frequency_days: int = 7
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
                    sources TEXT,
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
                """, (item.topic, item.frequency_days, json.dumps(item.sources), item.active))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
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
            conn.execute("UPDATE watchlist SET last_run = CURRENT_TIMESTAMP WHERE topic = ?", (topic,))
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
    parser = argparse.ArgumentParser(description="Watchlist management")
    subparsers = parser.add_subparsers(dest="command")
    
    add_parser = subparsers.add_parser("add", help="Add topic to watchlist")
    add_parser.add_argument("topic")
    add_parser.add_argument("--frequency", type=int, default=7)
    add_parser.add_argument("--sources", nargs="+", default=["web", "reddit"])
    
    list_parser = subparsers.add_parser("list", help="List watchlist")
    
    remove_parser = subparsers.add_parser("remove", help="Remove topic")
    remove_parser.add_argument("topic")
    
    run_parser = subparsers.add_parser("run", help="Run due items")
    
    args = parser.parse_args()
    manager = WatchlistManager()
    
    if args.command == "add":
        item = WatchlistItem(topic=args.topic, frequency_days=args.frequency, sources=args.sources)
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
            print(json.dumps({"action": "research", "topic": item.topic, "sources": item.sources}))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
