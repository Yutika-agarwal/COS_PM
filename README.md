# Chief of Staff for PM

A self-hosted **AI chief of staff**. Every 4 hours (or on demand) it reads your Slack, email,
meetings, docs and tickets through [Claude Code](https://claude.com/claude-code) and your MCP
servers, then gives you one structured briefing: what's urgent, what's blocked, which decisions
were never recorded, and what's coming up. It shows on a local dashboard and can DM you in Slack.

```
 Sources (MCP)            Claude Code (`claude -p`)           You
 ┌──────────────┐         ┌──────────────────────┐     ┌─────────────────┐
 │ Glean        │         │ reads your memory/   │     │ Local dashboard │
 │ Jira / Linear│  ───►   │ calls the MCP tools  │ ──► │ Slack DM (opt.) │
 │ Calendar ... │         │ synthesises → JSON   │     │ History         │
 └──────────────┘         └──────────────────────┘     └─────────────────┘
```

**Why it's easy to adopt:** the app has **no API keys of its own**. It runs `claude -p` as a
subprocess, which reuses the MCP connections and logins you already have in Claude Code
(including OAuth-based ones such as Glean). Pure Python standard library — nothing to `pip install`.

## Quick start (5 minutes)

**Requirements:** Python 3.9+, [Claude Code](https://claude.com/claude-code) installed and logged in
(run `claude` once), and at least one MCP source connected (see below).

```bash
git clone <this-repo-url> chief-of-staff-for-pm
cd chief-of-staff-for-pm

# 1. Try it with fictional data first — no Claude needed
python3 -m cos serve --demo          # open http://localhost:5050

# 2. Make it yours
cp config.example.json config.json   # choose your sources
cp -r memory.example memory          # then edit the 3 files — this is what makes briefings useful
cp .env.example .env                 # optional: Slack webhook

# 3. Connect your sources (pick one or both)
#    Glean:  docs/GLEAN.md          Any other MCP:  docs/ADDING_SOURCES.md

# 4. Check setup, then run for real
python3 -m cos check
python3 -m cos serve                 # click "Generate Now"
```

Prefer to be guided? Open this folder in Claude Code and say **"set me up"** — [`CLAUDE.md`](CLAUDE.md)
tells Claude how to interview you, fill in the memory files and configure sources.

## What you get

| Briefing section | Contents |
|---|---|
| Summary | The 2–4 sentences that matter most right now |
| Urgent Actions | Ranked, with the reason and a recommended next step |
| Slack Highlights / Email | Items needing you, flagged `action` |
| Meeting Notes | Key points and action items from recent meetings |
| Project Updates | Status per project from your `memory/projects.md` |
| Coming Up | Next meetings/deadlines, flagged when prep is needed |

Plus a history sidebar, a countdown to the next run, auto catch-up after your laptop sleeps, and optional Slack delivery.

## Configure your sources

Sources are entries in `config.json` — plain-English instructions plus the name of the MCP server
Claude should use. No code changes needed.

```json
{ "id": "tickets", "enabled": true, "label": "Issue tracker",
  "mcp_server": "jira",
  "instructions": "List tickets assigned to me that changed in the lookback window or are blocked." }
```

- **Glean** (Slack + email + meetings + docs in one connector): [docs/GLEAN.md](docs/GLEAN.md)
- **Add any other MCP server** (Jira, Linear, Notion, Google Calendar, GitHub, …): [docs/ADDING_SOURCES.md](docs/ADDING_SOURCES.md)
- `python3 -m cos sources` lists what's configured; `python3 -m cos prompt` prints exactly what Claude will be asked.

## Commands

| Command | Does |
|---|---|
| `python3 -m cos serve [--demo]` | Dashboard + 4-hourly scheduler on `http://127.0.0.1:5050` |
| `python3 -m cos generate` | One briefing from the terminal (handy for cron) |
| `python3 -m cos check` | Diagnose config, CLI, memory, sources |
| `python3 -m cos sources` | List sources and pre-approved tools |
| `python3 -m cos prompt` | Print the full prompt (debug / tune) |
| `python3 -m cos test-slack` | Send a sample message to your webhook |

Tests: `python3 -m unittest discover -s tests`

## Privacy & safety

- Binds to `127.0.0.1` only; the generate endpoint rejects cross-site requests.
- `config.json`, `mcp.json`, `memory/`, `data/` and `.env` are git-ignored — your people, projects and
  briefings never get committed.
- Briefings contain content from your work systems. Treat `data/` as sensitive, and follow your
  company's policy on sending work data to AI tools and Slack webhooks.
- The prompt instructs Claude to use only retrieved information and to report failed sources
  under "Source issues" rather than guess. Still, verify before acting on anything important.
- Claude is pre-approved only for the MCP servers of **enabled** sources (`--allowedTools mcp__<server>`).

## Customising

- **Sections / tone / ranking rules:** edit `SYSTEM` and `SCHEMA` in `cos/engine.py`, and the matching renderer in `static/index.html`.
- **Cadence:** `interval_hours` and `lookback_hours` in `config.json`.
- **More memory:** any extra `memory/*.md` file is included automatically.
- **Recipes:** [docs/recipes/zoom-summaries.md](docs/recipes/zoom-summaries.md) — compile meeting AI summaries into a Word doc.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how it works and [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for fixes.

## License

MIT
