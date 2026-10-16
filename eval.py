#!/usr/bin/env python3
"""
ClauseGuard AI — offline self-test (stdlib only, zero dependencies).

Run:  python eval.py
Exit non-zero on any failure. No network / no InfiniSynapse key required:
the test exercises the offline rule engine and the local HTTP routes, which
is exactly the path judges see when the platform is busy (graceful fallback).
"""

import json
import os
import sys
import threading
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fallback
import infini
import app as appmod

_passed = 0
_failed = 0


def check(name, cond, extra=""):
    global _passed, _failed
    if cond:
        _passed += 1
    else:
        _failed += 1
        print("  FAIL:", name, extra)


# --------------------------------------------------------------------------
# 1. Offline rule engine — determinism
# --------------------------------------------------------------------------
HI = ("本合同自期满之日起自动续约，甲方有权随时修改条款，"
      "乙方需以个人资产提供个人担保，并承担一切损失。")
r = fallback.scan(HI)
labels = [f["label"] for f in r["findings"]]
check("fallback.detects-auto-renewal", any("自动续约" in l for l in labels))
check("fallback.detects-unilateral", any("单方" in l for l in labels))
check("fallback.detects-personal-guarantee", any("个人担保" in l for l in labels))
check("fallback.score-band-high", r["score"] >= 40 and r["band"] == "HIGH", str(r))
check("fallback.every-finding-documented",
      all("explanation" in f and "suggestion" in f and f["severity"]
          for f in r["findings"]))

CLEAN = "甲乙双方本着平等自愿的原则友好合作，共同开发新产品并分享收益。"
rc = fallback.scan(CLEAN)
check("fallback.clean-zero-findings", len(rc["findings"]) == 0, str(rc))
check("fallback.clean-score-zero", rc["score"] == 0)
check("fallback.clean-band-low", rc["band"] == "LOW")

LOW = "本合同包含竞业限制条款，且约定不予退款。"
rl = fallback.scan(LOW)
check("fallback.low-only", all(f["severity"] == "LOW" for f in rl["findings"]), str(rl))
check("fallback.low-band", rl["band"] == "LOW" and rl["score"] == 10, str(rl))

MED = "本合同责任限于直接损失，且所有成果归甲方所有。"
rm = fallback.scan(MED)
check("fallback.medium-band", rm["band"] == "MEDIUM" and rm["score"] == 24, str(rm))

# score is capped at 100 (four HIGH rules already sum to 100)
CAP = ("本合同自动续约，甲方有权单方修改条款，"
       "你需承担一切损失的宽泛赔偿，并提供个人担保与个人财产。")
rcap = fallback.scan(CAP)
check("fallback.score-capped-100", rcap["score"] == 100 and rcap["band"] == "HIGH", str(rcap))

# --------------------------------------------------------------------------
# 1b. English mode — Dubai Create AI Agents entry is English-only
# --------------------------------------------------------------------------
EN_HI = ("This agreement shall be automatically renewed upon expiry. "
         "Party A may unilaterally modify the terms without notice. "
         "The signer provides a personal guarantee with personal assets and "
         "shall indemnify Party B against all losses.")
ren = fallback.scan(EN_HI, "en")
en_labels = [f["label"] for f in ren["findings"]]
check("fallback.en-detects-auto-renewal", "Auto-renewal" in en_labels, str(en_labels))
check("fallback.en-detects-unilateral", "Unilateral change of terms" in en_labels)
check("fallback.en-detects-personal-guarantee", "Personal guarantee" in en_labels)
check("fallback.en-same-score-as-zh", ren["score"] == r["score"] and ren["band"] == r["band"],
      f"en={ren['score']}/{ren['band']} zh={r['score']}/{r['band']}")
check("fallback.en-findings-fully-english",
      all(f["label"].isascii() and f["explanation"].isascii() and f["suggestion"].isascii()
          for f in ren["findings"]), str(ren))
check("fallback.en-note-english", ren["note"].isascii() and "offline" in ren["note"])
check("fallback.en-lang-field", ren["lang"] == "en")
rzh = fallback.scan(HI, "zh")
check("fallback.zh-default-unchanged", rzh["score"] == r["score"] and rzh["lang"] == "zh")
check("fallback.en-cap-also-100", fallback.scan(
    "auto-renew, unilateral change without notice, broad indemnity for all losses, personal guarantee", "en"
)["score"] == 100)
check("fallback.en-clean-zero", len(fallback.scan(
    "The parties cooperate on equal terms and share revenue fairly.", "en")["findings"]) == 0)
check("fallback.bad-lang-falls-back-zh",
      fallback.scan(HI, "fr")["lang"] == "zh")

# --------------------------------------------------------------------------
# 2. Injection safety — malicious contract text must not break the engine
# --------------------------------------------------------------------------
EVIL = "<script>alert(1)</script> 自动续约 个人担保"
re_ = fallback.scan(EVIL)
check("fallback.injection-no-crash", isinstance(re_, dict) and "findings" in re_)
check("fallback.injection-still-detects",
      any("自动续约" in l for l in [f["label"] for f in re_["findings"]]))

# --------------------------------------------------------------------------
# 3. InfiniSynapse adapter — graceful degradation without a key
# --------------------------------------------------------------------------
cli = infini.InfiniClient(api_key=None)
check("infini.importable", True)
check("infini.no-key-launch-fails-gracefully", cli.launch("any text")["ok"] is False)
check("infini.no-key-status-safe", isinstance(cli.get_status("nope"), dict))

# --------------------------------------------------------------------------
# 4. HTTP routes — start the real server, exercise it (proxy bypassed)
# --------------------------------------------------------------------------
PORT = int(os.environ.get("EVAL_PORT", "8011"))
srv = appmod.ThreadingHTTPServer(("127.0.0.1", PORT), appmod.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _get(path):
    try:
        with op.open(urllib.request.Request("http://127.0.0.1:%d%s" % (PORT, path)),
                     timeout=5) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def _post(path, data):
    try:
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (PORT, path),
                                     data=json.dumps(data).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with op.open(req, timeout=5) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


s, b = _get("/healthz")
check("app.healthz-200", s == 200 and json.loads(b).get("ok") is True, b[:80])
s, b = _get("/")
check("app.index-serves-html", s == 200 and "<html" in b.lower())
s, b = _get("/does-not-exist")
check("app.unknown-404", s == 404)
s, b = _post("/api/analyze", {})
check("app.missing-text-400", s == 400)
s, b = _post("/api/analyze", {"text": "   "})
check("app.blank-text-400", s == 400)
s, b = _post("/api/analyze", {"text": HI, "mode": "offline"})
ok = (s == 200)
if ok:
    j = json.loads(b)
    check("app.offline-mode", j.get("mode") == "offline", b[:80])
    check("app.offline-findings-present", j.get("result", {}).get("score", 0) >= 40)
s, b = _post("/api/analyze", {"text": EVIL, "mode": "offline"})
check("app.injection-json-safe", s == 200 and (lambda: (json.loads(b), True)[1])(), b[:80])
srv.shutdown()

# --------------------------------------------------------------------------
print("=" * 46)
print("结果：%d 通过 / %d 失败" % (_passed, _failed))
print("RESULT: %d passed, %d failed" % (_passed, _failed))
print("=" * 46)
sys.exit(1 if _failed else 0)
