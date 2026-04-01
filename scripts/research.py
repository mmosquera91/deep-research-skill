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
        Returns search plan for agent to execute.
        """
        if sources is None:
            sources = ["web", "reddit", "youtube"]
        
        findings = []
        
        for source_name in sources:
            source = self.sources.get(source_name)
            if not source:
                continue
            
            if source_name == "reddit":
                query = source._build_query(topic, days)
            elif source_name == "youtube":
                query = source._build_query(topic)
            else:
                query = topic
            
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
        """Ingest web search results into storage."""
        source = self.sources.get(source_name)
        if not source:
            return 0
        
        if source_name == "reddit":
            results = source.parse_results(web_results)
        elif source_name == "youtube":
            results = source.parse_search_results(web_results)
        else:
            results = [source.parse_web_search_result(r) for r in web_results]
        
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
    
    research_parser = subparsers.add_parser("research", help="Research a topic")
    research_parser.add_argument("topic", help="Topic to research")
    research_parser.add_argument("--days", type=int, default=30, help="Days back to search")
    research_parser.add_argument("--sources", nargs="+", choices=["web", "reddit", "youtube", "all"],
                                default=["all"], help="Sources to search")
    
    stats_parser = subparsers.add_parser("stats", help="Show database stats")
    
    args = parser.parse_args()
    
    orchestrator = ResearchOrchestrator()
    
    if args.command == "research":
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