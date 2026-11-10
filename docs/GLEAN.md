# Connect Glean (Slack + email + meetings + docs in one connector)

[Glean](https://www.glean.com) indexes your company's apps. Its MCP server lets Claude search them all
with your own permissions, so one connection can cover Slack, email, meeting recordings/transcripts and Drive.

> Glean setups differ by company. Ask your Glean admin or internal IT docs for **your organisation's
> Glean MCP URL**, and check whether MCP access is enabled for your account.

## 1. Add the server to Claude Code

```bash
claude mcp add --transport http glean <YOUR-GLEAN-MCP-URL>
claude mcp list            # should show "glean"
```

Then start `claude`, run `/mcp`, select **glean** and complete the browser login (SSO / OAuth).
This is OAuth in the browser — **not** an API token. Once it works interactively, `claude -p`
(which this app uses) reuses the same session, so no credentials are stored in this repo.

Alternative: put the server in this repo's `mcp.json` (git-ignored) instead of your global Claude config:

```bash
cp mcp.example.json mcp.json    # edit the URL; keep the key name "glean"
```

## 2. Enable the source

In `config.json` keep the `glean` source enabled. `mcp_server` must equal the name you used above
(`glean`). Tune the instructions to your needs, for example:

```json
{
  "id": "glean", "enabled": true, "mcp_server": "glean",
  "label": "Slack, email, meetings and docs (via Glean)",
  "instructions": "Using Glean: (1) Slack DMs and mentions plus threads in #my-team and #my-launch-channel; (2) email from my manager and anything flagged; (3) meeting summaries and transcripts; (4) docs edited by my team. Highlight alerts that keep firing without an acknowledgement and decisions discussed but never written down."
}
```

## 3. Verify

```bash
python3 -m cos check
claude -p "Use Glean to find my 3 most recent Slack mentions" --allowedTools mcp__glean
python3 -m cos generate
```

If the test command can't see Glean, the MCP login hasn't been completed for non-interactive use — redo `/mcp`.

## No Glean?

Skip it. Disable the `glean` source and add individual MCP servers instead — see
[ADDING_SOURCES.md](ADDING_SOURCES.md). You can also mix: Glean for search plus a direct tracker MCP.
