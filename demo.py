#!/usr/bin/env python3
"""ClauseGuard AI — offline demo (stdlib only, zero dependencies).

Run:  python demo.py
Scans examples/sample_contract.txt with the offline bilingual rule engine,
prints the findings in English and Chinese, and asserts that both languages
return the same risk score (bilingual parity).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fallback  # noqa: E402

SAMPLE = os.path.join(HERE, "examples", "sample_contract.txt")


def main() -> int:
    with open(SAMPLE, "r", encoding="utf-8") as fh:
        text = fh.read()
    print("ClauseGuard AI — offline bilingual scan")
    print("sample : examples/sample_contract.txt (freelance agreement)")
    print("-" * 64)
    results = {}
    for lang in ("en", "zh"):
        result = fallback.scan(text, lang)
        results[lang] = result
        print("[%s] risk score %d/100 (%s) — %d finding(s)" % (
            lang, result["score"], result["band"], len(result["findings"])))
        for f in result["findings"]:
            print("  %-4s %-18s %s" % (f["severity"], f["label"], f["suggestion"]))
        print()
    if results["en"]["score"] != results["zh"]["score"]:
        print("FAIL: bilingual parity broken (%s vs %s)" % (
            results["en"]["score"], results["zh"]["score"]))
        return 1
    print("OK: bilingual parity holds (both %d/100)" % results["en"]["score"])
    print(json.dumps({"score": results["en"]["score"],
                      "band": results["en"]["band"],
                      "findings": len(results["en"]["findings"])},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
