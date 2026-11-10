"""Briefing engine.

Builds a prompt from (memory files + enabled sources + output schema) and runs
`claude -p` as a subprocess. Claude Code then uses whatever MCP servers the user
has connected (Glean, Jira, Slack, ...) and inherits their existing auth, so this
app needs no API keys of its own.
"""
import json
import re
import shlex
import subprocess
from datetime import datetime

from .config import enabled_sources

SCHEMA = """{
  "summary": "2-4 sentence executive summary: the single most important things right now",
  "urgent_actions": [{"title": "", "detail": "", "when": "Today|This week|<date>", "source": ""}],
  "slack_highlights": [{"title": "", "detail": "", "action": false}],
  "email": [{"title": "", "detail": "", "action": false}],
  "meeting_notes": [{"title": "", "bullets": [""], "actions": [""]}],
  "project_updates": [{"id": "", "title": "", "status": "on_track|at_risk|blocked|done", "detail": ""}],
  "coming_up": [{"when": "", "title": "", "prep_needed": false}],
  "source_errors": ["<source id>: what failed, if anything"]
}"""

SYSTEM = """You are the user's Chief of Staff. Your job is to synthesize everything that
happened across their information streams into a briefing they can read in five minutes.

Rules:
- Use ONLY information you actually retrieved with your tools. Never invent items, names,
  ticket keys, dates or quotes. If a source returns nothing, say so in source_errors or leave the section empty.
- Lead with what needs a decision or action from the user. Rank urgent_actions by impact, most urgent first.
- Surface gaps: decisions discussed but never recorded, owners missing, blocked people, alerts that kept firing.
- Be specific: name the person, ticket, service or document, and say what to do next.
- Prefer one clear sentence per item. No filler.
- Respect the user's memory files (who they are, who matters, what projects are active).
- Output ONE JSON object matching the schema, and nothing else (no markdown fences, no commentary)."""


def read_memory(memory_dir):
    parts = []
    for name in ("context.md", "people.md", "projects.md"):
        p = memory_dir / name
        if p.exists():
            parts.append(f"### memory/{name}\n{p.read_text().strip()}")
    for p in sorted(memory_dir.glob("*.md")) if memory_dir.exists() else []:
        if p.name not in ("context.md", "people.md", "projects.md"):
            parts.append(f"### memory/{p.name}\n{p.read_text().strip()}")
    return "\n\n".join(parts) or "(no memory files found — briefing will be generic; see memory.example/)"


def build_prompt(cfg, now=None):
    now = now or datetime.now().astimezone()
    sources = enabled_sources(cfg)
    src_txt = "\n".join(
        f"{i}. [{s['id']}] {s.get('label', s['id'])}\n   {s.get('instructions', '').strip()}"
        for i, s in enumerate(sources, 1)) or "(no sources enabled)"
    return (
        f"{SYSTEM}\n\nCurrent time: {now.strftime('%A %Y-%m-%d %H:%M %Z')}\n"
        f"Lookback window: past {cfg['lookback_hours']} hours (older items only if still unresolved).\n\n"
        f"## About the user (memory)\n{read_memory(cfg['_memory_path'])}\n\n"
        f"## Sources to check\n{src_txt}\n\n"
        f"## Output schema\n{SCHEMA}\n")


def allowed_tools(cfg):
    """Pre-approve tools of each enabled source's MCP server so headless runs don't stall."""
    return [f"mcp__{s['mcp_server']}" for s in enabled_sources(cfg) if s.get("mcp_server")]


def build_command(cfg, prompt):
    c = cfg["claude"]
    cmd = shlex.split(c["command"]) + ["-p", prompt, "--output-format", "text"]
    if c.get("model"):
        cmd += ["--model", c["model"]]
    mcp = cfg.get("_mcp_path")
    if mcp and mcp.exists():
        cmd += ["--mcp-config", str(mcp)]
    cmd += list(c.get("extra_args") or [])
    tools = allowed_tools(cfg)
    if tools:  # variadic flag: keep it last so it can't swallow other args
        cmd += ["--allowedTools", ",".join(tools)]
    return cmd


def extract_json(text):
    """Pull the first balanced JSON object out of model output."""
    text = re.sub(r"```(?:json)?", "", text)
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                esc = (ch == "\\") and not esc
                if ch == '"' and not esc:
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except ValueError:
                        break
        start = text.find("{", start + 1)
    return None


def normalize(b):
    for k in ("urgent_actions", "slack_highlights", "email", "meeting_notes",
              "project_updates", "coming_up", "source_errors"):
        if not isinstance(b.get(k), list):
            b[k] = []
    b["summary"] = str(b.get("summary") or "")
    return b


def generate(cfg, runner=subprocess.run):
    prompt = build_prompt(cfg)
    cmd = build_command(cfg, prompt)
    try:
        r = runner(cmd, capture_output=True, text=True, timeout=cfg["claude"]["timeout_seconds"])
    except FileNotFoundError:
        raise RuntimeError(f"Claude Code CLI not found ('{cfg['claude']['command']}'). "
                           "Install it and run `claude` once to log in, or use --demo.")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Briefing timed out; raise claude.timeout_seconds in config.json")
    if r.returncode != 0:
        raise RuntimeError(f"claude exited {r.returncode}: {(r.stderr or r.stdout).strip()[:500]}")
    data = extract_json(r.stdout)
    if data is None:
        data = {"summary": r.stdout.strip()[:2000] or "Empty response from Claude.",
                "source_errors": ["Could not parse structured output; showing raw text."]}
    data = normalize(data)
    data["mode"] = "live"
    data["sources"] = [s["id"] for s in enabled_sources(cfg)]
    return data
