---
name: deep-research
description: Deep research across Reddit, YouTube, and web with recency filtering, watchlists, and briefings
version: 0.3.0
author: Miguel
argument-hint: research AI video tools, research watch add AI news, research briefing
---

# Deep Research Skill

Multi-source research engine for Hermes. Searches Reddit, YouTube, and web with **recency filters**, accumulates findings in SQLite, and supports **watchlists + briefings**.

The key idea: **do NOT do ad‑hoc `web_search` for deep research**.  
Instead, always delegate to this skill’s orchestrator, which:

1. Builds a search plan (with recency).
2. Ingests results into a persistent SQLite knowledge base.
3. Generates a rich synthesis prompt for the LLM.

---

## High-level behaviour (for agents)

When the user asks things like:

- `research <topic>`
- `deep research <topic>`
- “haz una investigación profunda sobre <topic>”
- “prepárame un briefing sobre <topic>”

the agent MUST:

1. **Call the deep-research orchestrator to get a plan.**  
2. **Execute the plan using `web_search`.**  
3. **Call the ingest endpoint to store results.**  
4. **Call the synthesis endpoint to generate the final report.**  

### Hard rules for Hermes / agents

- ❌ Do **NOT** manually construct `web_search` queries for deep research.
- ✅ ALWAYS call this skill’s `research` command first and follow its JSON plan.
- ✅ Use the `days` parameter for recency; **do not hardcode years** like `2025` in queries.
- ✅ After executing the plan, ALWAYS call ingestion and synthesis before answering.

---

## Commands (human + agent)

| Command                          | Description                               |
|----------------------------------|-------------------------------------------|
| `research <topic>`               | One-shot deep research across all sources |
| `research watch add <topic>`     | Add topic to watchlist                    |
| `research watch list`            | Show watchlist                            |
| `research watch remove <topic>`  | Remove from watchlist                     |
| `research watch run`             | Run all due items (for cron)             |
| `research briefing`              | Generate briefing from watchlist findings |
| `research history <query>`       | Search past findings                      |

Implementation is backed by these Python entrypoints:

- `python3 -m scripts.research research "<topic>" --days 30` → returns JSON plan.
- `python3 -m scripts.research ingest --topic "<topic>" --source <source> --results-file results.json` → ingests `web_search` results.
- `python3 -m scripts.synthesis --topic "<topic>"` → produces a **synthesis prompt** from all stored findings for that topic.

---

## Agent protocol: One-Shot Research

When the user asks: `research <topic>` or “deep research <topic>”:

### Step 1: Get a multi-source search plan

Call:

```bash
python3 -m scripts.research research "<topic>" --days 30
```

This returns JSON like:

```json
{
  "topic": "<topic>",
  "days": 30,
  "searches": [
    { "source": "web",    "query": "… after:YYYY-MM-DD", "status": "pending" },
    { "source": "reddit", "query": "… site:reddit.com after:YYYY-MM-DD", "status": "pending" },
    { "source": "youtube","query": "… site:youtube.com after:YYYY-MM-DD", "status": "pending" }
  ],
  "instruction": "Use web_search tool with each query, then call ingest_results()"
}
```

**Agent rule:**  
Use these `query` values **as-is**. They already include recency via `after:YYYY-MM-DD`.  
Do not add hardcoded years like `2025`; rely on `days`.

### Step 2: Execute the plan with `web_search`

For each entry in `result["searches"]`:

1. Call Hermes `web_search` with:
   - `query = search["query"]`
   - reasonable `limit` (e.g. 10)
2. Collect the raw `web_search` results (a `List[dict]`) into JSON.

Example pseudo-code:

```python
plan = skill_run("deep-research", "research", topic="<topic>", days=30)

for search in plan["searches"]:
    results = web_search(query=search["query"], limit=10)
    save results as JSON to /tmp/deep_research_<source>.json
    skill_run("deep-research", "ingest", topic=plan["topic"], source=search["source"], results_file="/tmp/deep_research_<source>.json")
```

### Step 3: Ingest results into SQLite

For each source, call:

```bash
python3 -m scripts.research ingest \
  --topic "<topic>" \
  --source <source_name> \
  --results-file /path/to/results.json
```

- `results-file` must contain the raw `web_search` results as a JSON list.
- The skill will:
  - Parse per source (Reddit, YouTube, web).
  - Deduplicate by URL.
  - Normalize topics.
  - Store findings in `~/.local/share/deep-research/research.db`.

### Step 4: Generate synthesis prompt and answer

Finally, call:

```bash
python3 -m scripts.synthesis --topic "<topic>"
```

This:

- Loads all findings for `<topic>` (respecting recency configured in the store).
- Calculates metadata (total findings, distribution by source, date range, engagement score share).
- Generates a **synthesis prompt** with:
  - Metadata
  - Source distribution
  - Top findings per source (links + snippets)
  - Clear instructions for: patterns, developments, sentiment, actionable insights, source reliability.

**Agent:**  
Take the string returned by `scripts.synthesis` as the **system+user prompt** for the final LLM call, and answer the user with that synthesized report.

---

## Watchlist Management (agents + cron)

### Add to Watchlist

When user says “watch this topic” or “track this regularly”:

```bash
python3 -m scripts.watchlist add "Topic Name" --frequency 7 --sources reddit youtube web
```

### Run Due Items (cron-friendly)

For scheduled runs:

```bash
python3 -m scripts.watchlist run
```

This prints JSON lines like:

```json
{"action": "research", "topic": "AI coding tools", "sources": ["reddit", "youtube", "web"]}
```

**Agent:** para cada línea:

1. Llama a `research` con el `topic` y `sources` dados.
2. Ejecuta el plan (`web_search` → `ingest`).
3. Opcional: llama a `synthesis` y envía un briefing al usuario.

### Cron Setup

```python
cronjob(
  action="create",
  schedule="0 9 * * *",
  prompt="Run deep-research watchlist",
  skill="deep-research"
)
```

---

## Database Location

```text
~/.local/share/deep-research/
├── research.db      # Findings storage (with FTS)
└── watchlist.db     # Watchlist configuration
```

---

## Dependencies

- Python 3.11+
- SQLite3 (stdlib)
- Hermes tools: `web_search`, `web_extract`, `youtube-content`