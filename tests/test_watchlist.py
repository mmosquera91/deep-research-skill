import pytest
import tempfile
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.watchlist import WatchlistManager, WatchlistItem

def test_add_and_list_items():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "watchlist.db")
        manager = WatchlistManager(db_path)
        
        item = WatchlistItem(
            topic="AI news",
            frequency_days=7,
            sources=["reddit", "youtube"]
        )
        
        manager.add(item)
        items = manager.list_all()
        
        assert len(items) == 1
        assert items[0].topic == "AI news"
        assert items[0].frequency_days == 7

def test_duplicate_topic():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "watchlist.db")
        manager = WatchlistManager(db_path)
        
        item = WatchlistItem(topic="Unique topic", frequency_days=7)
        assert manager.add(item) == True
        assert manager.add(item) == False  # Duplicate
