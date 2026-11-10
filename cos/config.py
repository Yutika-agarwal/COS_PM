"""Configuration loading. Everything company/user specific lives in config.json,
.env and memory/ — all git-ignored."""
import copy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULTS = {
    "port": 5050,
    "interval_hours": 4,
    "lookback_hours": 4,
    "memory_dir": "memory",
    "data_dir": "data",
    "claude": {
        "command": "claude",
        "model": None,
        "mcp_config": "mcp.json",
        "extra_args": [],
        "timeout_seconds": 900,
    },
    "notify": {"slack": True, "webhook_env": "SLACK_WEBHOOK_URL"},
    "sources": [],
}


def load_dotenv(path=None):
    """Tiny .env loader (no python-dotenv dependency). Does not override real env."""
    path = Path(path or ROOT / ".env")
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _resolve(p):
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def load_config(path=None):
    load_dotenv()
    path = Path(path or os.environ.get("COS_CONFIG") or ROOT / "config.json")
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        path = ROOT / "config.example.json"
    cfg = _merge(DEFAULTS, json.loads(path.read_text()))
    cfg["_path"] = str(path)
    if os.environ.get("COS_PORT"):
        cfg["port"] = int(os.environ["COS_PORT"])
    cfg["memory_dir"] = os.environ.get("COS_MEMORY_DIR", cfg["memory_dir"])
    cfg["data_dir"] = os.environ.get("COS_DATA_DIR", cfg["data_dir"])
    cfg["_memory_path"] = _resolve(cfg["memory_dir"])
    cfg["_data_path"] = _resolve(cfg["data_dir"])
    mcp = cfg["claude"].get("mcp_config")
    cfg["_mcp_path"] = _resolve(mcp) if mcp else None
    return cfg


def enabled_sources(cfg):
    return [s for s in cfg["sources"] if s.get("enabled", True)]
