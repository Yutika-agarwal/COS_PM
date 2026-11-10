# Troubleshooting

| Symptom | Fix |
|---|---|
| `Claude Code CLI not found` | Install Claude Code; ensure `claude` is on PATH, or set `claude.command` in `config.json` |
| Briefing says a source failed / is empty | Run `claude mcp list`; make `mcp_server` match the name exactly; redo OAuth via `/mcp` |
| Works interactively but not from the app | The tool isn't pre-approved or login expired. `python3 -m cos sources` shows allowed tools; re-login via `/mcp` |
| Timed out | Raise `claude.timeout_seconds`, or reduce/sharpen sources |
| "Could not parse structured output" | Claude returned prose; the raw text is shown. Re-run; shorten instructions; check `python3 -m cos prompt` |
| Generic, unhelpful briefing | Fill in `memory/*.md` with real names, project keys, channels |
| Tickets belong to someone else | Your tracker source instructions need *your* name/keys — see `memory/projects.md` |
| No Slack DM | `python3 -m cos test-slack`; check `.env`, and that the URL starts with `https://hooks.slack.com/` |
| Port in use | `COS_PORT=5051 python3 -m cos serve` |
| Runs stop after laptop sleep | They resume on wake (catch-up). For always-on, run on an always-on machine |
