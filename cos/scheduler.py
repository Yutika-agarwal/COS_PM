"""Runs briefings every N hours and on demand. Catches up after the machine sleeps."""
import threading
import time
import traceback
from datetime import datetime, timedelta, timezone

from . import demo, engine
from .notifier import notify


class Scheduler:
    def __init__(self, cfg, store, demo_mode=False):
        self.cfg, self.store, self.demo_mode = cfg, store, demo_mode
        self.interval = timedelta(hours=cfg["interval_hours"])
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self.running = False
        self.last_error = None
        self.last_notify = None
        latest = store.latest()
        self.last_run = datetime.fromisoformat(latest["generated_at"]) if latest else None

    # ---- state -------------------------------------------------------
    def next_run(self):
        return (self.last_run + self.interval) if self.last_run else datetime.now(timezone.utc)

    def is_due(self, now=None):
        now = now or datetime.now(timezone.utc)
        return self.last_run is None or now >= self.last_run + self.interval

    def status(self):
        return {
            "running": self.running,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run().isoformat(),
            "interval_hours": self.cfg["interval_hours"],
            "last_error": self.last_error,
            "last_notify": self.last_notify,
            "mode": "demo" if self.demo_mode else "live",
            "sources": [s["id"] for s in self.cfg["sources"] if s.get("enabled", True)],
        }

    # ---- work --------------------------------------------------------
    def run_once(self):
        """Generate one briefing. Returns saved briefing, or None if one is already running."""
        if not self._lock.acquire(blocking=False):
            return None
        self.running = True
        try:
            data = demo.generate(self.cfg) if self.demo_mode else engine.generate(self.cfg)
            saved = self.store.save(data)
            self.last_run = datetime.fromisoformat(saved["generated_at"])
            self.last_error = None
            if not self.demo_mode:
                sent, msg = notify(self.cfg, saved)
                self.last_notify = {"sent": sent, "message": msg}
            return saved
        except Exception as e:  # noqa: BLE001
            self.last_error = str(e)
            traceback.print_exc()
            self.last_run_attempt = datetime.now(timezone.utc)
            return None
        finally:
            self.running = False
            self._lock.release()

    def trigger_async(self):
        if self.running:
            return False
        threading.Thread(target=self.run_once, daemon=True).start()
        return True

    def loop(self):
        backoff_until = None
        while not self._stop.wait(30):
            now = datetime.now(timezone.utc)
            if backoff_until and now < backoff_until:
                continue
            if self.last_run is None and self.cfg["_path"].endswith("config.example.json"):
                continue  # fresh clone: wait for the user to configure and click Generate
            if self.is_due(now) and not self.running:
                if self.run_once() is None and self.last_error:
                    backoff_until = now + timedelta(minutes=15)  # don't hammer after failures
                else:
                    backoff_until = None

    def start(self):
        threading.Thread(target=self.loop, daemon=True).start()

    def stop(self):
        self._stop.set()
