# Setup guide for Claude Code

This repo is **Chief of Staff for PM**. When the user says "set me up" (or similar), do the following.
Be conversational, ask one thing at a time, and never invent facts about the user.

1. **Run `python3 -m cos check`** and summarise what's missing.
2. **Create local config** (all git-ignored): `cp config.example.json config.json`, `cp -r memory.example memory`, `cp .env.example .env`.
3. **Interview the user** to fill `memory/context.md` (name, role, team, email, Slack member ID, time zone,
   focus areas, briefing preferences), `memory/people.md` (manager, key stakeholders, who they cover for)
   and `memory/projects.md` (active projects with real tracker keys, status, milestones, services/channels to watch).
   Offer to bootstrap `projects.md` from a planning doc they point you to — only use what the doc says.
4. **Sources.** Run `claude mcp list`. For each tool the user wants (Glean, tracker, calendar, …):
   - If it's already connected, set `"enabled": true` and make `mcp_server` match the name from `claude mcp list`.
   - If not, follow `docs/GLEAN.md` or `docs/ADDING_SOURCES.md`. OAuth logins need the user to complete a browser step — tell them when.
   - Tune each source's `instructions` with their real project keys, channels and team names.
5. **Optional Slack delivery:** walk through `docs/SLACK_WEBHOOK.md`. The webhook URL is a secret —
   have the user paste it into `.env` themselves; don't print or commit it.
6. **Verify:** `python3 -m cos check`, then `python3 -m cos serve`, and have the user click *Generate Now*.
   If the briefing mentions failed sources, fix those before finishing.

Rules: never commit `config.json`, `mcp.json`, `memory/`, `data/` or `.env`. Don't add company-specific names,
URLs or ticket keys to tracked files — they belong in the git-ignored files above.
