# ClauseGuard Justice — Contract-Risk Agent for Legal Aid Access

**Track 07 — Timely Justice / Legal Backlog** · Code for a Billion (Bharat Agentic-AI Hackathon 2026, Code for India)

An autonomous **contract-risk agent** built for people who meet a lawyer *too late*.
Paste a contract (English or Chinese); the agent returns every high-risk clause
**quoted verbatim**, a plain-language explanation of the harm, a concrete fix,
and a quantified 0–100 risk score — with **assertion-tested parity** between
languages. It runs with **zero API key and zero cost** (offline rule engine),
which is exactly the constraint legal-aid work operates under.

> Demo tool · not legal advice.

---

## The problem (why this track)

India's courts carry one of the world's largest backlogs — on the order of
**tens of millions of pending cases** (widely reported at ~52 million; verify
against live NJDG data before submission). A large share of that load begins
long before a courthouse: in contracts that non-lawyers signed without
understanding — auto-renewal traps, unlimited indemnity, one-sided
non-refundable clauses, unilateral termination.

The people the backlog hurts most — legal-aid beneficiaries — rarely reach a
lawyer *before* signing, and cannot afford per-document LLM API budgets.
Between "sign here" and "first hearing" there is no cheap, plain-language way
to learn what a document actually does to you.

**This agent closes that gap.** Triage at the moment of signing; explain in
plain language; quantify risk. Fewer surprise disputes tomorrow is fewer cases
in the queue the day after.

## How it works

```
Browser -> app backend -> InfiniSynapse LLM API (SSE + newTask)   [primary]
                       -> offline bilingual rule engine            [resilience]
```

- **Quote-then-explain**: every finding quotes the clause verbatim, explains
  the harm in plain language, and gives a concrete fix. No unattributed advice.
- **Quantified triage**: a 0–100 risk score ranks clauses so a reader (or a
  busy legal-aid paralegal) sees the most dangerous terms first.
- **Bilingual by construction**: the full interface and every finding switch
  language with one click; the same contract scores **identically** in both
  languages (assertion-tested).
- **Always runnable**: if the LLM API is unavailable, the local rule engine
  takes over seamlessly — no key, no network, no budget.
- **Zero third-party dependencies** — pure Python standard library
  (`urllib` + `http.server`), runs anywhere, fully auditable.

## Judging criteria — evidence, not intentions

Code for a Billion scores 25% each on problem size, severity, solution
quality, and **proven impact** (deployment data). Where this project stands:

| Criterion | Evidence in this repo |
|---|---|
| Problem size (25%) | Judicial-backlog scale documented above; contract disputes are a recurring civil-litigation source; legal-aid access gap is structural (no pre-signing triage tool exists at zero cost) |
| Severity (25%) | `examples/sample_contract.txt` is a realistic freelance agreement with auto-renewal, indemnity, and non-refundable traps — each mapped to a concrete financial harm |
| Solution quality (25%) | 36 assertions in `eval.py` (bilingual score parity, finding completeness, HTTP routes, hostile-input handling); CI green on Python 3.10/3.11/3.12 |
| Proven impact (25%) | Deployed demo link + 30s walkthrough video (`clauseguard_demo.mp4`); deployment records (`/healthz` probes) kept with the submission |

## Run it in 30 seconds (no key needed)

```bash
python app.py
# open http://localhost:8000
```

1. Copy the contents of [`examples/sample_contract.txt`](examples/sample_contract.txt)
2. Paste into the textarea, press **Analyze**
3. Every finding quotes the clause, explains the risk, and gives a fix — the
   same contract in English and Chinese returns the same 0–100 score

Command-line equivalent (offline engine, no server, no key):

```bash
python demo.py    # scans examples/sample_contract.txt in EN + ZH, asserts parity
```

## Self-verification

```bash
python eval.py    # 36 assertions, exit non-zero on any failure
```

Exercises the offline rule engine and local HTTP routes — exactly the path
judges see when the platform is busy (graceful fallback). Runs on any Python
3.10+; no dependencies, no network, no key.

## Deploy

`app.py` reads `PORT` and binds `0.0.0.0`; expose `/healthz`. Render-ready:
connect the repo, `python app.py`, done. Optional: set `INFINI_KEY` for the
LLM path; without it the offline engine serves every request.

## License

MIT — see [`LICENSE`](LICENSE). Released open-source so any NGO, legal-aid
body, or government agency can adopt and extend it.

## Entry checklist for the hackathon

See [`CODE_FOR_A_BILLION.md`](CODE_FOR_A_BILLION.md) — event rules (verified
from the official page), submission checklist, and the four-criteria mapping
used throughout this README.
