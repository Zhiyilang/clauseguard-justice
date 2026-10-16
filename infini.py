"""
InfiniSynapse Server API adapter (zero-dependency, stdlib only).

Implements the officially documented flow:
  Frontend -> Our backend -> InfiniSynapse adapter -> InfiniSynapse Server API
The API Key NEVER leaves the server. We connect the SSE event stream FIRST,
then send `newTask` (order must not be reversed, per the Vibe Coding Guide).
"""

import os
import json
import uuid
import time
import threading
import urllib.request
import urllib.error


class InfiniClient:
    def __init__(self, api_key=None, base=None, console=None):
        self.api_key = api_key or os.environ.get("INFINI_KEY")
        self.base = (base or os.environ.get("INFINI_BASE")
                     or "https://app.infinisynapse.com").rstrip("/")
        self.console = (console or os.environ.get("INFINI_CONSOLE")
                        or "https://api.infinisynapse.com/api").rstrip("/")
        self.lang = os.environ.get("INFINI_LANG", "zh_CN")
        self._proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        # task_key (connId) -> dict(state, partial, final, taskId, done, error)
        self._store = {}
        self._lock = threading.Lock()

    # ---- low-level helpers -------------------------------------------------
    def _opener(self):
        if self._proxy:
            ph = urllib.request.ProxyHandler({"https": self._proxy, "http": self._proxy})
            return urllib.request.build_opener(ph)
        return urllib.request.build_opener()

    def _headers(self, extra=None):
        h = {"Authorization": f"Bearer {self.api_key}", "x-lang": self.lang}
        if extra:
            h.update(extra)
        return h

    # ---- auth / account ----------------------------------------------------
    def validate(self):
        try:
            req = urllib.request.Request(
                f"{self.console}/user/profile", headers=self._headers())
            with self._opener().open(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            return {"error": str(e)}

    # ---- SSE reader (runs in a background thread) --------------------------
    def _sse_reader(self, conn_id, task_key, max_seconds=220):
        url = f"{self.base}/api/ai/events?connId={conn_id}"
        deadline = time.time() + max_seconds
        try:
            req = urllib.request.Request(
                url, headers=self._headers({"Accept": "text/event-stream"}))
            resp = self._opener().open(req, timeout=max_seconds + 10)
            etype = None
            for raw in resp:
                if time.time() > deadline:
                    break
                line = raw.decode("utf-8", "replace").rstrip("\r\n")
                if line.startswith("event:"):
                    etype = line[6:].strip()
                elif line.startswith("data:"):
                    data = line[5:].strip()
                    try:
                        j = json.loads(data)
                    except Exception:  # noqa: BLE001
                        j = None
                    if etype == "message.partial" and isinstance(j, dict):
                        chunk = j.get("data") or j.get("text") or ""
                        if isinstance(chunk, str):
                            with self._lock:
                                cur = self._store.setdefault(task_key, {})
                                cur["partial"] = cur.get("partial", "") + chunk
                    done_marker = (
                        etype == "state.ready"
                        or (isinstance(j, dict)
                            and j.get("type") in ("state.ready", "completion_result"))
                    )
                    if done_marker:
                        with self._lock:
                            self._store.setdefault(task_key, {})["done"] = True
                        return
        except Exception as e:  # noqa: BLE001
            with self._lock:
                self._store.setdefault(task_key, {})["sse_error"] = f"SSE: {e}"
        finally:
            with self._lock:
                self._store.setdefault(task_key, {})["done"] = True

    # ---- launch a task -----------------------------------------------------
    def launch(self, text, max_retry=2):
        if not self.api_key:
            return {"ok": False, "error": "INFINI_KEY 未配置"}
        conn_id = str(uuid.uuid4())
        task_key = conn_id
        with self._lock:
            self._store[task_key] = {"state": "starting", "partial": "", "done": False}
        # 1) connect SSE first
        threading.Thread(target=self._sse_reader, args=(conn_id, task_key),
                        daemon=True).start()
        time.sleep(2)
        # 2) send newTask (retries on 500 / network errors)
        body = json.dumps({"type": "newTask", "text": text, "connId": conn_id}).encode("utf-8")
        last_err = None
        for i in range(max_retry):
            try:
                req = urllib.request.Request(
                    f"{self.base}/api/ai/message", data=body,
                    headers=self._headers({"Content-Type": "application/json"}))
                with self._opener().open(req, timeout=40) as r:
                    js = json.loads(r.read().decode("utf-8"))
                    if js.get("code") == 200:
                        tid = js.get("data", {}).get("taskId") or js.get("taskId")
                        with self._lock:
                            self._store[task_key]["taskId"] = tid
                            self._store[task_key]["state"] = "running"
                        return {"ok": True, "connId": conn_id, "taskId": tid}
                    last_err = f"code {js.get('code')}: {js.get('message')}"
            except Exception as e:  # noqa: BLE001
                last_err = f"ERR {e}"
            if i < max_retry - 1:
                time.sleep(4 * (i + 1))
        with self._lock:
            self._store[task_key]["state"] = "error"
            self._store[task_key]["error"] = last_err or "unknown"
            self._store[task_key]["done"] = True
        return {"ok": False, "error": last_err}

    # ---- fetch final result (called once done) -----------------------------
    def fetch_result(self, task_key):
        with self._lock:
            info = dict(self._store.get(task_key, {}))
        tid = info.get("taskId")
        if tid:
            try:
                req = urllib.request.Request(
                    f"{self.base}/api/ai_task/getUiMessageById?id={tid}",
                    headers=self._headers())
                with self._opener().open(req, timeout=30) as r:
                    js = json.loads(r.read().decode("utf-8"))
                final = self._extract_final(js)
                with self._lock:
                    self._store[task_key]["final"] = final or info.get("partial", "")
                    self._store[task_key]["ui"] = js.get("data")
            except Exception as e:  # noqa: BLE001
                with self._lock:
                    if not self._store[task_key].get("final"):
                        self._store[task_key]["final"] = info.get("partial", "")
                    self._store[task_key]["fetch_error"] = str(e)
        with self._lock:
            return dict(self._store.get(task_key, {}))

    @staticmethod
    def _extract_final(js):
        data = js.get("data", {}) if isinstance(js, dict) else {}
        # try several known shapes
        for key in ("messages", "list", "items"):
            msgs = data.get(key)
            if isinstance(msgs, list):
                best = ""
                for m in msgs:
                    if not isinstance(m, dict):
                        continue
                    c = m.get("content") or m.get("text") or m.get("message") or ""
                    if isinstance(c, str) and len(c) > len(best):
                        best = c
                if best:
                    return best
        # fallback: whole data as string
        if isinstance(data, str) and data:
            return data
        return ""

    def get_status(self, task_key):
        with self._lock:
            info = dict(self._store.get(task_key, {}))
        if info.get("done") and not info.get("final") and info.get("taskId"):
            return self.fetch_result(task_key)
        return info
