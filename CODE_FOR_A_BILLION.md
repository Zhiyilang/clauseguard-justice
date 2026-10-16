# Code for a Billion — Entry Checklist

**Event**: Code for a Billion — Bharat Agentic-AI Hackathon 2026 (Code for India)
**Track**: 07 — Timely Justice / Legal Backlog
**Official page**: https://codeforindia.org/hackathon (rules below verified from it, 2026-10-16)

## Hard rules (official)

| Rule | Detail |
|---|---|
| Eligibility | "Anyone, anywhere on Earth" (official FAQ) — open to China-based participants |
| Cost | Free; 1M smart-code tokens on AgentFoundry.me per participant |
| Deadline | **2026-11-15** — project deployed to any cloud + open-sourced; winners 2026-12-05 |
| Prize | Per track: 1st ₹1,50,000 / 2nd ₹1,00,000 / 3rd ₹50,000 (pool ₹18 lakh) |
| License | Apache-2.0 or MIT, released to the Code for India GitHub org (contributor attribution retained) |
| Submission | Public GitHub repo + README + 2–3 min demo video (or live link) + GitHub issue form |
| Judging | 25% problem size / 25% severity / 25% solution quality / 25% **proven deployed impact** |

## Why this project fits Track 07

Official track scope: *case triage, document summarisation, legal aid access,
court scheduling efficiency.*

- **document summarisation** → every finding quotes the clause verbatim and explains it in plain language (EN/ZH)
- **case triage** → 0–100 risk score surfaces the most dangerous clauses first
- **legal aid access** → zero-cost, keyless offline engine: the exact constraint legal-aid users live under
- **prevention** → contract disputes are a recurring civil-litigation source; triage at signing reduces future backlog

## Submission checklist

- [x] Public repo with README (problem statement + four-criteria evidence table)
- [x] MIT LICENSE
- [x] Zero-dependency runnable agent (`python app.py` / `python demo.py`)
- [x] 36-assertion self-test, CI green (Python 3.10/3.11/3.12)
- [x] Demo video (`clauseguard_demo.mp4`, 30s — extend to 2–3 min for final submission)
- [ ] Deploy to any cloud (Render free tier: `python app.py`, reads `PORT`, `/healthz`)
- [ ] User registers at AgentFoundry.me and creates the project entry
- [ ] Copy of this repo pushed under the Code for India GitHub org (MIT)
- [ ] Submit via the official GitHub issue form before 2026-11-15

## Deployment sequencing note

The WorkBuddy sites slot currently hosts the MatchLens demo for a separate
competition (deadline 2026-10-21). **After** that submission is confirmed,
re-point the slot at this repo's `app.py` to produce the live deployment link
CFB judging requires ("proven impact" = deployment data, not intentions).

## Open questions for the organizers (post in official Discussions)

1. Repo flow: keep canonical repo under our org (MIT) + push copy under the CFI GitHub org before deadline — acceptable?
2. AgentFoundry.me is unreachable from mainland China; judging states "deployed to any cloud" — can development happen outside the AF IDE with the repo + live link judged? Happy to import if access is restored.
