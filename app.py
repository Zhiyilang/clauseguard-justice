#!/usr/bin/env python3
"""
ClauseGuard AI — Contract Risk Analyzer on InfiniSynapse.

Zero-dependency web app (Python stdlib only):
  - Serves a single-page frontend (index.html)
  - Launches contract analysis via the InfiniSynapse Server API (SSE + newTask)
  - Falls back to a local offline rule engine if the API is unavailable,
    so the app is ALWAYS runnable (contest requirement).

Run:  INFINI_KEY=sk-xxxx python app.py
Then open http://localhost:8000
"""

import os
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import infini
import fallback


def _load_env_file():
    """Minimal .env loader (stdlib only) so the deploy sandbox can supply INFINI_KEY
    without relying on injected environment variables. Never printed/leaked."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(p):
        return
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:  # noqa: BLE001
        pass


_load_env_file()

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
CLIENT = infini.InfiniClient()

ROOT = os.path.dirname(os.path.abspath(__file__))


def render_index():
    path = os.path.join(ROOT, "index.html")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


INDEX_HTML = render_index()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._send(200, INDEX_HTML, "text/html; charset=utf-8")
            return
        if self.path == "/healthz":
            self._send(200, json.dumps({"ok": True}))
            return
        if self.path.startswith("/api/status/"):
            key = self.path.split("/api/status/", 1)[1].strip()
            info = CLIENT.get_status(key)
            # normalise for the frontend
            out = {
                "state": info.get("state", "unknown"),
                "done": info.get("done", False),
                "partial": info.get("partial", ""),
                "final": info.get("final", ""),
                "error": info.get("error"),
            }
            self._send(200, json.dumps(out, ensure_ascii=False))
            return
        self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path != "/api/analyze":
            self._send(404, json.dumps({"error": "not found"}))
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:  # noqa: BLE001
            self._send(400, json.dumps({"ok": False, "error": "bad json"}))
            return

        text = (payload.get("text") or "").strip()
        if not text:
            self._send(400, json.dumps({"ok": False, "error": "合同文本为空"}))
            return

        lang = payload.get("lang", "zh")
        if lang not in ("zh", "en"):
            lang = "zh"
        mode = payload.get("mode", "auto")  # auto | infinisynapse | offline

        # Path A: explicit offline demo
        if mode == "offline":
            result = fallback.scan(text, lang)
            self._send(200, json.dumps({"ok": True, "mode": "offline", "result": result},
                                       ensure_ascii=False))
            return

        # Path B: InfiniSynapse (primary)
        if lang == "en":
            prompt = (
                "You are a meticulous contract-review lawyer. Review the contract "
                "text below, list every high-risk clause by severity (HIGH/MEDIUM/LOW), "
                "explain each risk in plain language, and give a concrete fix. End with "
                "an overall risk score from 0-100 and a one-line verdict. Use clear "
                "Markdown headings.\n\n===== CONTRACT BODY =====\n" + text
            )
        else:
            prompt = (
                "你是一名严谨的合同审查律师。请审阅下面这份合同文本，"
                "识别高风险条款，按严重程度（HIGH/MEDIUM/LOW）列出每一条，"
                "用大白话解释风险点，并给出修改建议。最后给出一个 0-100 的风险评分和总体结论。"
                "请使用 Markdown 结构清晰输出。\n\n===== 合同正文 =====\n" + text
            )
        launched = CLIENT.launch(prompt)
        if launched.get("ok"):
            self._send(200, json.dumps({
                "ok": True, "mode": "infinisynapse", "connId": launched["connId"],
            }, ensure_ascii=False))
            return

        # Path C: graceful offline fallback (API unavailable)
        result = fallback.scan(text, lang)
        self._send(200, json.dumps({
            "ok": True, "mode": "offline", "offline_reason": launched.get("error"),
            "result": result,
        }, ensure_ascii=False))

    def log_message(self, fmt, *args):
        sys.stderr.write("[clauseguard] " + (fmt % args) + "\n")


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"ClauseGuard AI running on http://{HOST}:{PORT}")
    print("InfiniSynapse key configured:", "YES" if CLIENT.api_key else "NO (offline mode only)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
