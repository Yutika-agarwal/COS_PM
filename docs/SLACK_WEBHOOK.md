# Deliver briefings to Slack (optional)

1. Go to <https://api.slack.com/apps> → **Create New App** → **From scratch**.
2. Name it "Chief of Staff", pick your workspace → **Create App**.
   (Some workspaces require admin approval for new apps.)
3. Sidebar → **Incoming Webhooks** → toggle **Activate Incoming Webhooks** on.
4. **Add New Webhook to Workspace** → under *Direct Messages* choose **yourself** → **Allow**.
5. Copy the URL (`https://hooks.slack.com/services/...`) and add it to `.env`:

   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
   ```
6. Test: `python3 -m cos test-slack` — you should get a DM.

Every live briefing is then posted automatically. Disable with `"notify": {"slack": false}` in `config.json`.
The webhook URL is a secret: never commit `.env`. Demo mode never sends to Slack.
