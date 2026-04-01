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

## Project Structure

```
skills/deep-research/
├── SKILL.md              # Hermes skill definition
├── README.md             # This file
├── scripts/
│   ├── research.py       # Main orchestrator
│   ├── storage.py        # SQLite backend
│   ├── watchlist.py      # Watchlist management
│   ├── synthesis.py      # LLM prompt generation
│   └── sources/
│       ├── base.py       # Abstract adapter
│       ├── web.py        # Web search
│       ├── reddit.py     # Reddit search
│       └── youtube.py    # YouTube search
└── tests/                # Unit tests
```

## Development

Run tests:
```bash
cd skills/deep-research
pytest tests/ -v
```

## License

MIT
