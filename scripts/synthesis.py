"""
Synthesis of research findings into reports.
This module provides prompts/templates for LLM synthesis.
"""

from typing import List, Dict
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import ResearchFinding

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


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Synthesis engine")
    parser.add_argument("--topic", help="Topic to generate prompt for")
    parser.add_argument("--db", help="Database path")
    args = parser.parse_args()
    
    if args.topic:
        from storage import ResearchStore
        store = ResearchStore(args.db)
        findings = store.find_by_topic(args.topic)
        
        engine = SynthesisEngine()
        prompt = engine.generate_prompt(args.topic, findings)
        print(prompt)
    else:
        parser.print_help()
