#!/usr/bin/env python3
"""
Deep research orchestrator.
Called by Hermes agent with access to tools.
"""

import sys
import json
import argparse
from typing import List, Optional

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

        print(
            f"[deep-research] Building search plan for topic='{topic}' days={days} sources={sources}",
            file=sys.stderr,
        )

        searches = []

        for source_name in sources:
            source = self.sources.get(source_name)
            if not source:
                continue

            params = source.get_search_params(topic, days)
            searches.append(
                {
                    "source": source_name,
                    "query": params["query"],
                    "status": "pending",
                }
            )

        plan = {
            "topic": topic,
            "days": days,
            "searches": searches,
            "instruction": "Use web_search tool with each query, then call ingest_results()",
        }

        return plan

    def ingest_results(self, topic: str, source_name: str, web_results: List[dict]) -> int:
        """Ingest web search results into storage."""
        source = self.sources.get(source_name)
        if not source:
            print(f"[deep-research] Unknown source '{source_name}', skipping", file=sys.stderr)
            return 0

        print(
            f"[deep-research] Ingesting {len(web_results)} raw results for topic='{topic}' source='{source_name}'",
            file=sys.stderr,
        )

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
                metadata=r.metadata,
            )
            if self.store.save_finding(finding):
                count += 1

        print(
            f"[deep-research] Saved {count} new findings for topic='{topic}' source='{source_name}'",
            file=sys.stderr,
        )

        return count

    def get_findings(self, topic: str, days: Optional[int] = None) -> List[ResearchFinding]:
        """Retrieve findings for a topic."""
        return self.store.find_by_topic(topic, days)


def main():
    parser = argparse.ArgumentParser(description="Deep research tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # research: build plan
    research_parser = subparsers.add_parser("research", help="Build research plan for a topic")
    research_parser.add_argument("topic", help="Topic to research")
    research_parser.add_argument("--days", type=int, default=30, help="Days back to search")
    research_parser.add_argument(
        "--sources",
        nargs="+",
        choices=["web", "reddit", "youtube", "all"],
        default=["all"],
        help="Sources to search",
    )

    # ingest: ingest web_search results
    ingest_parser = subparsers.add_parser("ingest", help="Ingest web_search results into database")
    ingest_parser.add_argument("--topic", required=True, help="Topic the results belong to")
    ingest_parser.add_argument(
        "--source",
        required=True,
        choices=["web", "reddit", "youtube"],
        help="Source name (web/reddit/youtube)",
    )
    ingest_parser.add_argument(
        "--results-file",
        help="Path to JSON file with web_search results (list[dict]). If omitted, read from stdin.",
    )

    # stats: show DB stats
    stats_parser = subparsers.add_parser("stats", help="Show database stats")

    args = parser.parse_args()
    orchestrator = ResearchOrchestrator()

    if args.command == "research":
        sources = ["web", "reddit", "youtube"] if "all" in args.sources else args.sources
        plan = orchestrator.research(args.topic, args.days, sources)
        print(json.dumps(plan, indent=2))

    elif args.command == "ingest":
        # Read results from file or stdin
        if args.results_file:
            with open(args.results_file, "r", encoding="utf-8") as f:
                web_results = json.load(f)
        else:
            raw = sys.stdin.read()
            web_results = json.loads(raw) if raw.strip() else []

        count = orchestrator.ingest_results(args.topic, args.source, web_results)
        print(json.dumps({"topic": args.topic, "source": args.source, "saved": count}, indent=2))

    elif args.command == "stats":
        stats = orchestrator.store.get_stats()
        print(json.dumps(stats, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()