"""CLI:  python -m cos [serve|generate|check|sources|test-slack] [--demo] [--config FILE]"""
import argparse
import json
import os
import shutil
import shlex
import sys

from . import demo
from .config import enabled_sources, load_config
from .engine import allowed_tools, build_prompt
from .notifier import notify
from .scheduler import Scheduler
from .server import serve
from .store import Store


def cmd_check(cfg):
    ok = True

    def line(good, msg, fix=""):
        nonlocal ok
        ok &= bool(good)
        print(("  ✓ " if good else "  ✗ ") + msg + (f"\n      → {fix}" if fix and not good else ""))

    print(f"Config: {cfg['_path']}")
    line(not cfg["_path"].endswith("config.example.json"), "config.json exists",
         "cp config.example.json config.json")
    claude = shlex.split(cfg["claude"]["command"])[0]
    line(shutil.which(claude), f"Claude Code CLI found ('{claude}')", "Install Claude Code, then run `claude` once to log in")
    mem = cfg["_memory_path"]
    for n in ("context.md", "people.md", "projects.md"):
        line((mem / n).exists(), f"memory/{n}", "cp -r memory.example memory  (then edit the files)")
    srcs = enabled_sources(cfg)
    line(srcs, f"{len(srcs)} source(s) enabled: {', '.join(s['id'] for s in srcs) or 'none'}",
         "Set \"enabled\": true on at least one source in config.json")
    mcp = cfg["_mcp_path"]
    servers = {}
    if mcp and mcp.exists():
        try:
            servers = json.loads(mcp.read_text()).get("mcpServers", {})
        except ValueError:
            line(False, f"{mcp.name} is valid JSON", "Fix the JSON syntax")
        print(f"  • MCP servers in {mcp.name}: {', '.join(servers) or 'none'}")
    else:
        print("  • No mcp.json — relying on MCP servers already configured in Claude Code (`claude mcp list`)")
    for s in srcs:
        name = s.get("mcp_server")
        if name and servers and name not in servers:
            print(f"  ! source '{s['id']}' expects MCP server '{name}' which is not in {mcp.name} "
                  "(fine if it is configured in Claude Code itself)")
    url = os.environ.get(cfg["notify"]["webhook_env"], "")
    print(f"  • Slack delivery: {'configured' if url else 'not configured (optional)'}")
    print("\nAll good." if ok else "\nFix the ✗ items above, or try `python -m cos serve --demo`.")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cos", description=__doc__)
    ap.add_argument("command", nargs="?", default="serve",
                    choices=["serve", "generate", "check", "sources", "prompt", "test-slack"])
    ap.add_argument("--demo", action="store_true", help="use fictional sample data; no Claude needed")
    ap.add_argument("--config")
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    demo_mode = a.demo or os.environ.get("COS_DEMO") == "1"

    if a.command == "check":
        return cmd_check(cfg)
    if a.command == "sources":
        for s in cfg["sources"]:
            print(f"{'on ' if s.get('enabled', True) else 'off'}  {s['id']:<12} mcp={s.get('mcp_server', '-'):<10} {s.get('label', '')}")
        print("allowed tools:", ", ".join(allowed_tools(cfg)) or "none")
        return 0
    if a.command == "prompt":
        print(build_prompt(cfg))
        return 0
    if a.command == "test-slack":
        ok, msg = notify(cfg, demo.generate())
        print(msg)
        return 0 if ok else 1

    store = Store(cfg["_data_path"])
    sched = Scheduler(cfg, store, demo_mode=demo_mode)
    if a.command == "generate":
        saved = sched.run_once()
        if not saved:
            print("Failed:", sched.last_error, file=sys.stderr)
            return 1
        print(saved["summary"])
        return 0
    sched.start()
    serve(cfg, store, sched, a.host)
    return 0


if __name__ == "__main__":
    sys.exit(main())
