"""Briefing history stored as one JSON file per briefing."""
import json
from datetime import datetime, timezone
from pathlib import Path


class Store:
    def __init__(self, data_dir):
        self.dir = Path(data_dir) / "briefings"
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, briefing):
        now = datetime.now(timezone.utc)
        bid = now.strftime("%Y%m%dT%H%M%S%fZ")
        briefing = dict(briefing, id=bid, generated_at=now.isoformat())
        tmp = self.dir / f".{bid}.tmp"
        tmp.write_text(json.dumps(briefing, indent=2))
        tmp.replace(self.dir / f"{bid}.json")
        return briefing

    def get(self, bid):
        if not bid.replace("T", "").replace("Z", "").isdigit():
            return None  # reject path traversal / junk
        p = self.dir / f"{bid}.json"
        return json.loads(p.read_text()) if p.exists() else None

    def list(self, limit=100):
        out = []
        for p in sorted(self.dir.glob("*.json"), reverse=True)[:limit]:
            try:
                b = json.loads(p.read_text())
            except ValueError:
                continue
            out.append({
                "id": b["id"],
                "generated_at": b["generated_at"],
                "summary": (b.get("summary") or "")[:140],
                "mode": b.get("mode", ""),
            })
        return out

    def latest(self):
        items = self.list(1)
        return self.get(items[0]["id"]) if items else None
