<div align="center">

# 🔬 Deep Research Skill

### *Multi-source research engine with persistent memory for Hermes Agent*

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg?style=for-the-badge)](https://github.com/mmosquera91/deep-research-skill/releases)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-8%2F8%20passing-success.svg?style=for-the-badge)](./tests)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Hermes](https://img.shields.io/badge/Hermes-Agent-purple.svg?style=for-the-badge)](https://hermes-agent.nousresearch.com/)

<p align="center">
  <img src="https://img.shields.io/badge/Reddit-FF4500?style=flat-square&logo=reddit&logoColor=white" />
  <img src="https://img.shields.io/badge/YouTube-FF0000?style=flat-square&logo=youtube&logoColor=white" />
  <img src="https://img.shields.io/badge/Web-4285F4?style=flat-square&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white" />
</p>

</div>

---

## 🎯 Why Deep Research?

> **"`web_search` has the memory of a goldfish — results disappear. `deep-research` has the memory of an elephant — it accumulates, connects, and evolves."**

Traditional search is **stateless**. You search, see results, and they're gone. Deep Research is **stateful** — it builds a persistent knowledge base that grows smarter over time.

| Feature | `web_search` | `deep-research` |
|---------|-------------|-----------------|
| **Persistence** | ❌ Results vanish | ✅ SQLite storage |
| **Multi-source** | ❌ One query = one source | ✅ Reddit + YouTube + Web |
| **Recency Filter** | ⚠️ Limited | ✅ Last 7/30/90 days |
| **Synthesis** | ❌ Raw only | ✅ LLM-powered reports |
| **Watchlists** | ❌ One-shot | ✅ Cron scheduling |
| **Trend Detection** | ❌ Impossible | ✅ Temporal analysis |

---

## ✨ Features

<p align="center">
  <img width="800" alt="deep-research-overview" src="https://user-images.githubusercontent.com/placeholder/deep-research-banner.png">
</p>

### 🔍 Multi-Source Intelligence
- **Reddit** — Real developer opinions and discussions
- **YouTube** — Tutorial and review content with transcript extraction
- **Web** — Articles, blogs, and documentation

### 💾 Persistent Storage
All findings stored in **SQLite** with:
- Full-text search capabilities
- Automatic deduplication (URL-based)
- Temporal indexing for trend analysis
- Cross-source correlation

### 📊 Smart Synthesis
Automatically generates:
- **Pattern Recognition** — Themes across sources
- **Sentiment Analysis** — Community mood tracking
- **Actionable Insights** — What you should know/do
- **Source Reliability** — Signal vs noise ratings

### 📅 Watchlist System
```bash
# Track topics automatically
research watch add "AI coding tools" --frequency 7

# Get morning briefings
research briefing

# Schedule with cron
cronjob create "0 9 * * *" "Run daily research briefing"
```

---

## 🚀 Quick Start

### Installation

```bash
# Install from GitHub
hermes skills install git+https://github.com/mmosquera91/deep-research-skill

# Or manually clone
git clone https://github.com/mmosquera91/deep-research-skill.git
cp -r deep-research-skill ~/.hermes/skills/
```

### One-Shot Research

```bash
# Research a topic immediately
$ research "AI coding tools 2025"

🔬 Researching: AI coding tools 2025
📚 Found 9 findings
   Reddit: 3 | YouTube: 3 | Web: 3
💾 Saved to database
📊 Generating synthesis...
```

### Watchlist Management

```bash
# Add topic to watchlist
$ research watch add "OpenAI news" --frequency 7 --sources reddit youtube

✅ Added 'OpenAI news' to watchlist (checking every 7 days)

# List tracked topics
$ research watch list
✓ OpenAI news (every 7d)
✓ AI coding tools (every 7d)

# Generate briefing from all watchlist items
$ research briefing
📊 Morning Briefing — 2 topics, 15 new findings
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DEEP RESEARCH ENGINE                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🔍 SOURCES        💾 STORAGE          🧠 SYNTHESIS         │
│  ┌─────────┐      ┌──────────┐       ┌─────────────┐       │
│  │ Reddit  │──────│          │       │   LLM       │       │
│  ├─────────┤      │  SQLite  │◄──────│  Prompts    │       │
│  │ YouTube │──────│  Engine  │       │             │       │
│  ├─────────┤      │          │       │ • Patterns  │       │
│  │   Web   │──────│          │       │ • Sentiment │       │
│  └─────────┘      └──────────┘       │ • Insights  │       │
│                          ▲           └─────────────┘       │
│                          │                                  │
│                   📋 WATCHLIST                              │
│                   ┌─────────────┐                          │
│                   │ • Cron jobs │                          │
│                   │ • Frequency │                          │
│                   │ • Topics    │                          │
│                   └─────────────┘                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📖 Usage Examples

### Example 1: Technology Tracking

Track the evolution of "local LLMs" over 3 months:

```bash
# Week 1: Initial research
research "local LLM deployment 2025"
# → 12 findings saved

# Week 4: Follow-up research  
research "local LLM deployment 2025"
# → 8 new findings, 4 duplicates detected

# Generate trend report
research history "local LLM"
# → "Mention of Ollama +50%, GPT4All declining"
```

### Example 2: Competitive Intelligence

Monitor what developers say about your competitors:

```bash
# Add to watchlist
research watch add "Cursor AI reviews" --frequency 3 --sources reddit

# Daily briefings show sentiment shifts
research briefing
# → "Sentiment: 70% positive (was 45% last week)"
```

### Example 3: Pre-Decision Research

Before choosing a tech stack:

```bash
# Deep dive on options
research "Next.js vs Remix 2025"
research "self-hosted vs cloud database"

# Query accumulated knowledge
research history "performance comparison"
```

---

## 🛠️ Configuration

### Environment Variables

```bash
# Custom database location (optional)
export DEEP_RESEARCH_DB_PATH="/custom/path/research.db"
```

### Data Storage

```
~/.local/share/deep-research/
├── research.db          # Findings storage
│   ├── findings table   # URL, title, content, source, timestamp
│   ├── indexes on topic, source, created_at
│   └── full-text search on title + content
│
└── watchlist.db         # Watchlist configuration
    ├── topics table     # Topic, frequency, last_run
    └── active flag      # Enable/disable tracking
```

---

## 🧪 Testing

```bash
cd ~/.hermes/skills/deep-research

# Run all tests
pytest tests/ -v

# Output:
# tests/test_storage.py::test_store_init_creates_db PASSED
# tests/test_storage.py::test_save_and_retrieve PASSED
# tests/test_sources.py::test_source_result_creation PASSED
# tests/test_sources.py::test_web_source_search PASSED
# tests/test_sources.py::test_reddit_source PASSED
# tests/test_sources.py::test_youtube_source PASSED
# tests/test_watchlist.py::test_add_and_list_items PASSED
# tests/test_watchlist.py::test_duplicate_topic PASSED
#
# 8 passed in 0.12s
```

---

## 📚 Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `research <topic>` | One-shot research | `research "AI agents"` |
| `research watch add <topic>` | Add to watchlist | `research watch add "OpenAI" --frequency 7` |
| `research watch list` | Show watchlist | — |
| `research watch remove <topic>` | Remove from watchlist | — |
| `research watch run` | Run due items (cron) | — |
| `research briefing` | Generate briefing | — |
| `research history <query>` | Search past findings | `research history "Cursor"` |

---

## 🎯 Use Cases

<p align="center">
  <table>
    <tr>
      <td align="center">👨‍💻 <b>Developers</b></td>
      <td align="center">📊 <b>Founders</b></td>
      <td align="center">✍️ <b>Creators</b></td>
      <td align="center">🎓 <b>Researchers</b></td>
    </tr>
    <tr>
      <td>Technology tracking</td>
      <td>Competitive intel</td>
      <td>Content curation</td>
      <td>Literature review</td>
    </tr>
    <tr>
      <td>Stack decisions</td>
      <td>Market trends</td>
      <td>Trend detection</td>
      <td>Source synthesis</td>
    </tr>
  </table>
</p>

---

## 🔮 Roadmap

- [ ] Twitter/X source integration
- [ ] Hacker News source adapter
- [ ] YouTube transcript extraction (via youtube-content skill)
- [ ] Export to Markdown/PDF reports
- [ ] Web dashboard for findings visualization
- [ ] Collaborative research (shared databases)

---

## 🤝 Contributing

Contributions welcome! Areas where help is needed:

- Additional source adapters (Twitter, HN, Discord)
- Better synthesis prompts
- Export formats (Markdown, PDF, Notion)
- Performance optimizations

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built for [Hermes Agent](https://hermes-agent.nousresearch.com/) by Nous Research. Compatible with the [agentskills.io](https://agentskills.io) open standard.

---

<div align="center">

**[⬆ Back to Top](#-deep-research-skill)**

Made with 🔬 by Miguel

</div>
