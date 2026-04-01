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
skill_view("youtube-content")
# Then use transcript functionality
```

### Step 3: Store Findings

```python
# Save to research database
python3 -m scripts.research ingest --topic "topic" --source reddit --results ...
```

### Step 4: Synthesize

Generate synthesis prompt and pass to LLM:

```python
python3 -m scripts.synthesis --topic "topic"
```

## Watchlist Management

### Add to Watchlist

```python
python3 -m scripts.watchlist add "Topic Name" --frequency 7 --sources reddit youtube
```

### List Watchlist

```python
python3 -m scripts.watchlist list
```

### Run Due Items (for cron)

```python
python3 -m scripts.watchlist run
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
