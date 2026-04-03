"""
Synthesis of research findings into reports.
This module provides prompts/templates for LLM synthesis.
"""

from typing import List, Dict
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import ResearchFinding, ResearchStore


class SynthesisEngine:
    """Generates synthesis prompts for LLM."""

    def _calculate_metadata(self, findings: List[ResearchFinding]) -> dict:
        """Calculate metadata statistics for findings."""
        if not findings:
            return {"total": 0, "by_source": {}, "date_range": None, "with_score": 0}

        # Count by source
        by_source: Dict[str, int] = {}
        for f in findings:
            by_source[f.source] = by_source.get(f.source, 0) + 1

        # Count findings with score
        with_score = sum(1 for f in findings if f.score is not None)

        # Date range (if published_at available)
        dates = [f.published_at for f in findings if f.published_at]
        date_range = None
        if dates:
            try:
                parsed_dates = []
                for d in dates:
                    if isinstance(d, str):
                        try:
                            parsed_dates.append(datetime.fromisoformat(d.replace("Z", "+00:00")))
                        except Exception:
                            continue
                    elif isinstance(d, datetime):
                        parsed_dates.append(d)

                if parsed_dates:
                    date_range = {
                        "oldest": min(parsed_dates).strftime("%Y-%m-%d"),
                        "newest": max(parsed_dates).strftime("%Y-%m-%d"),
                    }
            except Exception:
                pass

        return {
            "total": len(findings),
            "by_source": by_source,
            "date_range": date_range,
            "with_score": with_score,
        }

    def _format_source_distribution(self, by_source: Dict[str, int]) -> str:
        """Format source distribution as ASCII bar chart."""
        if not by_source:
            return " (No data)"

        total = sum(by_source.values())
        max_val = max(by_source.values())
        max_label_len = max(len(s) for s in by_source.keys())

        lines = []
        for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
            bar_len = int((count / max_val) * 20) if max_val > 0 else 0
            bar = "█" * bar_len
            pct = (count / total) * 100
            lines.append(f" {source:<{max_label_len}} │{bar:<20}│ {count:>3} ({pct:>4.1f}%)")

        return "\n".join(lines)

    def generate_prompt(self, topic: str, findings: List[ResearchFinding]) -> str:
        """Generate synthesis prompt for findings with rich metadata."""

        # Calculate metadata
        meta = self._calculate_metadata(findings)

        # Group by source
        by_source: Dict[str, List[ResearchFinding]] = {}
        for f in findings:
            by_source.setdefault(f.source, []).append(f)

        # Build findings summary by source
        findings_text = []
        key_sources = []
        for source, items in by_source.items():
            findings_text.append(f"\n## {source.upper()}")
            for item in items[:5]:  # Top 5 per source
                findings_text.append(f"- [{item.title}]({item.url})")
                # recopila títulos+URLs para sección Key Sources
                key_sources.append((item.title, item.url))
                if item.score:
                    findings_text.append(f" Score: {item.score}")
                findings_text.append(f" {item.content[:200]}...")

        # Limita Key Sources a 5 únicos
        seen_urls = set()
        key_sources_dedup = []
        for title, url in key_sources:
            if url not in seen_urls:
                seen_urls.add(url)
                key_sources_dedup.append((title, url))
            if len(key_sources_dedup) >= 5:
                break

        # Build metadata section
        total = meta["total"]
        with_score = meta["with_score"]

        score_pct = (with_score / total * 100) if total > 0 else 0.0

        # Frase de apertura basada exactamente en meta['total'] y rango de fechas
        if meta["date_range"]:
            intro_line = (
                f"Based strictly on **{total} findings** stored in the deep-research "
                f"SQLite database for this topic between {meta['date_range']['oldest']} "
                f"and {meta['date_range']['newest']}, synthesize the evidence below."
            )
        else:
            intro_line = (
                f"Based strictly on **{total} findings** stored in the deep-research "
                f"SQLite database for this topic, synthesize the evidence below."
            )

        metadata_text = (
            f"📊 **Total Findings:** {total}\n"
            f"📈 **With Engagement Score:** {with_score} ({score_pct:.1f}%)\n"
        )
        if meta["date_range"]:
            metadata_text += (
                f"📅 **Date Range:** {meta['date_range']['oldest']} → "
                f"{meta['date_range']['newest']}\n"
            )

        source_dist = self._format_source_distribution(meta["by_source"])

        # Sección de Key Sources
        if key_sources_dedup:
            key_sources_text = "\n".join(
                f"- [{title}]({url})" for title, url in key_sources_dedup
            )
            # Lista de títulos sencilla para referenciar en el texto
            key_source_titles = ", ".join(
                f"“{title}”" for title, _ in key_sources_dedup
            )
        else:
            key_sources_text = "_No specific sources available_"
            key_source_titles = ""

        prompt = f"""You are a research analyst synthesizing findings on: **{topic}**

{intro_line}

## Metadata
{metadata_text}
## Source Distribution
{source_dist}

## Key Sources (Top references from the findings)
{key_sources_text}

## Raw Findings ({len(findings)} total)
{chr(10).join(findings_text)}

## Your Task
Synthesize these findings into a structured report. Follow these rules carefully:

1. Base your claims **only** on the Raw Findings above. Do not introduce external facts that are not supported by these findings.
2. When you mention a **concrete numeric detail** (prices, RAM, GitHub stars, dates, percentages),
   explicitly tag it with its source, for example:
   - "Jellyfin uses ~300MB RAM (from one of the Key Sources above)."
   - "Plex Pass costs $6.99/month (from a blog comparison in {key_source_titles})."
3. If you are **not sure** about an exact number from the findings:
   - Prefer qualitative language ("higher", "lower", "similar") or rough ranges ("≈", "~"),
   - or omit the number entirely instead of inventing it.
4. If you need to add general background context beyond the findings, label it explicitly as:
   - **Background (speculative):** <your extra context>
5. Prioritize patterns, events, and opinions that appear in multiple findings or sources.

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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Synthesis engine")
    parser.add_argument("--topic", help="Topic to generate prompt for")
    parser.add_argument(
        "--db",
        help="Database path (optional; default is ~/.local/share/deep-research/research.db)",
        default=None,
    )
    args = parser.parse_args()

    if args.topic:
        store = ResearchStore(args.db)
        findings = store.find_by_topic(args.topic)

        engine = SynthesisEngine()
        prompt = engine.generate_prompt(args.topic, findings)
        print(prompt)
    else:
        parser.print_help()
