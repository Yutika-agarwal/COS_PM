# Architecture

Three layers:

1. **Fetch** — not done by this app. `claude -p` calls your MCP tools (Glean, tracker, calendar …).
2. **Synthesis** — `cos/engine.py` builds one prompt from `memory/*.md`, the enabled sources and a JSON schema, runs Claude Code headlessly, and parses the JSON (falling back to showing raw text if parsing fails).
3. **Delivery** — `cos/server.py` serves `static/index.html`; `cos/notifier.py` optionally posts to Slack.

```
cos/config.py     config.json + .env loading (stdlib only)
cos/engine.py     prompt, command construction, JSON extraction
cos/scheduler.py  N-hourly + on-demand runs, single-flight lock, catch-up after sleep, 15-min backoff on failure
cos/store.py      one JSON file per briefing in data/briefings/
cos/server.py     localhost HTTP API + static dashboard
cos/notifier.py   Slack webhook
cos/demo.py       fictional sample data
```

## Why `claude -p` instead of calling APIs directly?

Many company search tools (Glean included) authenticate with browser OAuth, not API tokens, so a
standalone app can't call them. Claude Code already holds those sessions and runs the MCP tools
for you, so shelling out to it needs zero new credentials and works for anyone who already uses Claude Code.

## HTTP API

| Route | |
|---|---|
| `GET /api/status` | running, last/next run, last error, sources, mode |
| `GET /api/briefings` / `/latest` / `/<id>` | history, newest, one briefing |
| `POST /api/generate` | start a run (409 if one is already running) |

## Scheduling details

- Due when `now >= last_run + interval_hours`; `last_run` is read from the newest saved briefing, so restarts and laptop sleep don't lose cadence.
- On a fresh clone (no `config.json`, no briefings) it will not auto-run; click *Generate Now*.
- Run it in the background: `nohup python3 -m cos serve > cos.log 2>&1 &`, or use `python3 -m cos generate` from cron/launchd.
