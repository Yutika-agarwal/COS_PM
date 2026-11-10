import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cos import config as C, demo, engine, notifier  # noqa: E402
from cos.scheduler import Scheduler  # noqa: E402
from cos.server import make_handler  # noqa: E402
from cos.store import Store  # noqa: E402


def make_cfg(tmp, **over):
    mem = Path(tmp) / "memory"
    mem.mkdir(exist_ok=True)
    (mem / "context.md").write_text("Name: Test PM")
    (mem / "extra.md").write_text("Extra note")
    cfg = C._merge(C.DEFAULTS, {
        "sources": [
            {"id": "a", "enabled": True, "mcp_server": "srv_a", "label": "A", "instructions": "do A"},
            {"id": "b", "enabled": False, "mcp_server": "srv_b", "instructions": "do B"}],
        **over})
    cfg.update(_path="x.json", _memory_path=mem, _data_path=Path(tmp) / "data", _mcp_path=None)
    return cfg


class Engine(unittest.TestCase):
    def test_extract_json_variants(self):
        self.assertEqual(engine.extract_json('{"a": 1}'), {"a": 1})
        self.assertEqual(engine.extract_json('Sure!\n```json\n{"a": {"b": "}"}}\n```'), {"a": {"b": "}"}})
        self.assertEqual(engine.extract_json('x {bad} {"ok": true}'), {"ok": True})
        self.assertIsNone(engine.extract_json("no json"))

    def test_prompt_uses_memory_and_only_enabled_sources(self):
        with tempfile.TemporaryDirectory() as t:
            p = engine.build_prompt(make_cfg(t))
            self.assertIn("Test PM", p)
            self.assertIn("Extra note", p)
            self.assertIn("do A", p)
            self.assertNotIn("do B", p)

    def test_allowed_tools_only_enabled(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(engine.allowed_tools(make_cfg(t)), ["mcp__srv_a"])

    def test_command_includes_mcp_config_when_present(self):
        with tempfile.TemporaryDirectory() as t:
            cfg = make_cfg(t)
            mcp = Path(t) / "mcp.json"
            mcp.write_text("{}")
            cfg["_mcp_path"] = mcp
            cmd = engine.build_command(cfg, "hi")
            self.assertIn("--mcp-config", cmd)
            self.assertIn("mcp__srv_a", cmd)
            self.assertEqual(cmd[1], "-p")

    def test_generate_with_fake_runner(self):
        with tempfile.TemporaryDirectory() as t:
            cfg = make_cfg(t)
            out = 'Here:\n{"summary": "S", "urgent_actions": [{"title": "T"}]}'
            r = engine.generate(cfg, runner=lambda *a, **k: subprocess.CompletedProcess(a, 0, out, ""))
            self.assertEqual(r["summary"], "S")
            self.assertEqual(r["email"], [])  # normalized
            self.assertEqual(r["sources"], ["a"])

    def test_generate_unparseable_falls_back(self):
        with tempfile.TemporaryDirectory() as t:
            r = engine.generate(make_cfg(t), runner=lambda *a, **k: subprocess.CompletedProcess(a, 0, "plain text", ""))
            self.assertEqual(r["summary"], "plain text")
            self.assertTrue(r["source_errors"])

    def test_generate_failure_raises(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(RuntimeError):
                engine.generate(make_cfg(t), runner=lambda *a, **k: subprocess.CompletedProcess(a, 1, "", "boom"))

    def test_missing_cli_message(self):
        def boom(*a, **k):
            raise FileNotFoundError()
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(RuntimeError, "not found"):
                engine.generate(make_cfg(t), runner=boom)


class StoreSched(unittest.TestCase):
    def test_store_roundtrip_and_traversal(self):
        with tempfile.TemporaryDirectory() as t:
            s = Store(t)
            b = s.save(demo.generate())
            self.assertEqual(s.get(b["id"])["summary"], b["summary"])
            self.assertEqual(s.latest()["id"], b["id"])
            self.assertIsNone(s.get("../../etc/passwd"))

    def test_due_logic_and_demo_run(self):
        with tempfile.TemporaryDirectory() as t:
            cfg = make_cfg(t)
            sch = Scheduler(cfg, Store(cfg["_data_path"]), demo_mode=True)
            self.assertTrue(sch.is_due())
            self.assertIsNotNone(sch.run_once())
            self.assertFalse(sch.is_due())
            later = datetime.now(timezone.utc) + timedelta(hours=4, minutes=1)
            self.assertTrue(sch.is_due(later))

    def test_last_run_survives_restart(self):
        with tempfile.TemporaryDirectory() as t:
            cfg = make_cfg(t)
            st = Store(cfg["_data_path"])
            Scheduler(cfg, st, demo_mode=True).run_once()
            self.assertFalse(Scheduler(cfg, st, demo_mode=True).is_due())

    def test_single_flight(self):
        with tempfile.TemporaryDirectory() as t:
            cfg = make_cfg(t)
            sch = Scheduler(cfg, Store(cfg["_data_path"]), demo_mode=True)
            sch._lock.acquire()
            self.assertIsNone(sch.run_once())

    def test_failure_recorded(self):
        with tempfile.TemporaryDirectory() as t:
            cfg = make_cfg(t)
            cfg["claude"]["command"] = "definitely-not-a-real-binary-xyz"
            sch = Scheduler(cfg, Store(cfg["_data_path"]))
            self.assertIsNone(sch.run_once())
            self.assertIn("not found", sch.last_error)


class Notify(unittest.TestCase):
    def test_payload(self):
        p = notifier.build_payload(demo.generate())
        self.assertTrue(p["blocks"])
        json.dumps(p)

    def test_rejects_non_slack_url(self):
        with self.assertRaises(ValueError):
            notifier.send_slack(demo.generate(), "https://evil.example.com/x")

    def test_no_webhook_is_graceful(self):
        os.environ.pop("SLACK_WEBHOOK_URL", None)
        ok, msg = notifier.notify(C.DEFAULTS, demo.generate())
        self.assertFalse(ok)


class Server(unittest.TestCase):
    def test_api(self):
        from http.server import ThreadingHTTPServer
        with tempfile.TemporaryDirectory() as t:
            cfg = make_cfg(t)
            st = Store(cfg["_data_path"])
            sch = Scheduler(cfg, st, demo_mode=True)
            srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(st, sch))
            port = srv.server_address[1]
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{port}"
            try:
                def get(p):
                    return json.loads(urllib.request.urlopen(base + p).read())
                self.assertEqual(get("/api/status")["mode"], "demo")
                with self.assertRaises(urllib.error.HTTPError) as e:
                    urllib.request.urlopen(base + "/api/briefings/latest")
                self.assertEqual(e.exception.code, 404)
                sch.run_once()
                self.assertTrue(get("/api/briefings/latest")["summary"])
                self.assertEqual(len(get("/api/briefings")), 1)
                self.assertIn(b"Chief of Staff", urllib.request.urlopen(base + "/").read())
                for bad in ("/../config.example.json", "/%2e%2e/config.example.json", "/api/briefings/..%2f..%2fx"):
                    with self.assertRaises(urllib.error.HTTPError):
                        urllib.request.urlopen(base + bad)
                # CSRF: cross-origin POST rejected
                req = urllib.request.Request(base + "/api/generate", method="POST", headers={"Origin": "http://evil.example"})
                with self.assertRaises(urllib.error.HTTPError) as e:
                    urllib.request.urlopen(req)
                self.assertEqual(e.exception.code, 403)
                ok = urllib.request.urlopen(urllib.request.Request(base + "/api/generate", method="POST"))
                self.assertEqual(ok.status, 202)
            finally:
                srv.shutdown()


class Config(unittest.TestCase):
    def test_example_config_loads(self):
        cfg = C.load_config(C.ROOT / "config.example.json")
        self.assertTrue(cfg["sources"])
        self.assertEqual(cfg["interval_hours"], 4)

    def test_merge_is_deep(self):
        m = C._merge(C.DEFAULTS, {"claude": {"model": "x"}})
        self.assertEqual(m["claude"]["model"], "x")
        self.assertEqual(m["claude"]["command"], "claude")


if __name__ == "__main__":
    unittest.main()
