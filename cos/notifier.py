"""Optional Slack Incoming Webhook delivery."""
import json
import os
import urllib.request
from urllib.parse import urlparse


def _text(items, fmt):
    return "\n".join(fmt(i) for i in items) or "_Nothing_"


def build_payload(b):
    blocks = [{"type": "header", "text": {"type": "plain_text", "text": "⚡ Executive Briefing"}},
              {"type": "section", "text": {"type": "mrkdwn", "text": b.get("summary") or "_No summary_"}}]
    if b.get("urgent_actions"):
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text":
            "*🚨 Urgent Actions*\n" + _text(b["urgent_actions"],
                lambda a: f"• *{a.get('title','')}* _{a.get('when','')}_\n  {a.get('detail','')}")}})
    if b.get("coming_up"):
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text":
            "*📅 Coming Up*\n" + _text(b["coming_up"],
                lambda c: f"• {c.get('when','')} — {c.get('title','')}" + (" ⚠️ prep" if c.get("prep_needed") else ""))}})
    return {"text": "Executive Briefing: " + (b.get("summary") or "")[:100], "blocks": blocks[:50]}


def send_slack(briefing, webhook_url):
    host = urlparse(webhook_url).hostname or ""
    if not (host == "hooks.slack.com" or host.endswith(".slack.com")):
        raise ValueError("Webhook must be a hooks.slack.com URL")
    req = urllib.request.Request(webhook_url, json.dumps(build_payload(briefing)).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode()


def notify(cfg, briefing):
    """Returns (sent: bool, message: str). Never raises."""
    if not cfg["notify"].get("slack"):
        return False, "slack disabled"
    url = os.environ.get(cfg["notify"].get("webhook_env", "SLACK_WEBHOOK_URL"), "")
    if not url:
        return False, "no webhook configured"
    try:
        send_slack(briefing, url)
        return True, "sent"
    except Exception as e:  # noqa: BLE001
        return False, f"slack error: {e}"
