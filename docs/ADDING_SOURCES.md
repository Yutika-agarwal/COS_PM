# Add any MCP server as a source

A **source** is just: *an MCP server Claude can call* + *plain-English instructions for what to pull*.
You never edit Python to add one.

## 1. Connect the MCP server to Claude Code

Pick whichever fits:

**A. Globally in Claude Code**
```bash
claude mcp add --transport http <name> <url>          # remote HTTP/OAuth servers
claude mcp add <name> -- npx -y <some-mcp-package>    # local stdio servers
claude mcp list
```

**B. Only for this app** — add it to `mcp.json` (copy from `mcp.example.json`; git-ignored). It uses the
standard Claude Code format and is passed with `--mcp-config`:

```json
{
  "mcpServers": {
    "glean":    { "type": "http",  "url": "https://example.invalid/mcp" },
    "tracker":  { "type": "http",  "url": "https://example.invalid/tracker-mcp" },
    "calendar": { "command": "npx", "args": ["-y", "some-calendar-mcp"], "env": { "TOKEN": "${CALENDAR_TOKEN}" } }
  }
}
```

Complete any OAuth login once interactively (`claude` → `/mcp`). Keep secrets in env vars, not in the file.

## 2. Add a source entry to `config.json`

```json
{
  "id": "tickets",
  "enabled": true,
  "label": "Issue tracker",
  "mcp_server": "tracker",
  "instructions": "List tickets assigned to me or my team that changed in the lookback window, are unassigned in triage, blocked, or overdue. Project keys: see memory/projects.md."
}
```

| Field | Meaning |
|---|---|
| `id` | Short unique name; shown on the dashboard and in `source_errors` |
| `enabled` | `false` keeps the entry but skips it |
| `label` | Human description |
| `mcp_server` | Must match the key in `claude mcp list` / `mcp.json`. Its tools are pre-approved for headless runs (`mcp__<name>`). Omit for sources needing no MCP |
| `instructions` | What to fetch and what counts as important. Be specific: channels, project keys, names |

## 3. Test

```bash
python3 -m cos sources     # confirm it's listed with the right server and allowed tools
python3 -m cos check
python3 -m cos prompt      # see exactly what Claude is told
python3 -m cos generate    # real run; the briefing's "Source issues" lists anything that failed
```

## Ideas

| Want | Typical MCP | Example instruction |
|---|---|---|
| Tickets | Jira, Linear, GitHub | "Tickets I own that moved status, plus untriaged ones in project ABC" |
| Calendar | Google/Outlook Calendar | "Next 48h meetings; flag ones needing prep" |
| Docs | Drive, Notion, Confluence | "Docs my team edited today; anything with open comments for me" |
| Metrics / alerts | Datadog, Grafana, PagerDuty | "Alerts that fired in the last 24h and are still unacknowledged" |
| Code | GitHub | "PRs waiting on my review; releases cut this week" |

## Notes

- More sources = longer runs. Raise `claude.timeout_seconds` if a run times out.
- Prefer a few precise sources over many vague ones.
- Only sources with `enabled: true` are queried or pre-approved.
- Want a different output *section* (not just a new source)? Edit `SCHEMA` in `cos/engine.py` and the renderer in `static/index.html`.
