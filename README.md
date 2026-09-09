# ClauseGuard

ClauseGuard turns "read this whole contract and tell me if it's safe to sign"
into a 3-second, auditable clause-by-clause risk report — no lawyer required
for the first pass.

**Who it's for**: an operations/finance manager at a small company with no
in-house legal counsel, who currently either reads every incoming vendor
contract or outgoing customer agreement line-by-line, or pastes it into
ChatGPT ad hoc with no consistent checklist. See
[docs/CASE_STUDY.md](docs/CASE_STUDY.md) for the full assumed-user writeup
(this was built against synthetic/public-template contracts, not a real
company's paper — that assumption is stated explicitly, not hidden).

## What it does

Upload or paste a contract (`.txt`, `.docx`, or `.pdf`). ClauseGuard checks
it against a 10-category playbook (auto-renewal, liability caps,
indemnification, payment terms, IP ownership, confidentiality, governing
law, data privacy, assignment, non-compete) and returns:

- A risk level (Low / Medium / High / Critical) **per clause**, with the
  exact excerpt and the reason it's flagged
- A **next action**: Approve, Approve with conditions, Negotiate, or
  Escalate to legal
- A suggested redline for anything Medium risk or above
- A **Chat tab** to ask plain-English questions about that specific
  contract, grounded in its actual text
- Full contract history, with one-click delete when you're done with one

Every finding traces back to a specific, inspectable rule — this is not a
black box. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for why.

Multi-user accounts (sign up, log in), a **Playbook** tab showing exactly
what's checked for, and per-contract **Summary / Clauses / Chat** tabs are
all built in — see [docs/USER_GUIDE.md](docs/USER_GUIDE.md).

## Quick start (three steps)

```bash
git clone <this repo> && cd clauseguard
cp backend/.env.example backend/.env   # add a GEMINI_API_KEY if you have one -- optional, see below
docker-compose up
```

Then open **http://localhost:5174** and sign up (no email verification —
pick any username/password, 8+ characters). Every contract you review is
private to your account.

No API key is required to run the full pipeline — risk detection is 100%
rule-based. Without a key, redline/chat suggestions come from deterministic
templates instead of a live LLM call; with one, ClauseGuard uses Google
Gemini — see "What's real vs simulated" in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Repository layout

```
backend/    Django + DRF API (Knox token auth), rule-based clause analyzer, eval harness
frontend/   React + React Query UI
docs/       Architecture, evaluation results, case study, runbook, AI notes
docker-compose.yml   db (Postgres) + backend (Django) + frontend (React)
```

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) -- system design, data flow, schemas, trade-offs
- [docs/EVALUATION.md](docs/EVALUATION.md) -- test set, baseline comparison, failure analysis
- [docs/CASE_STUDY.md](docs/CASE_STUDY.md) -- problem, scope, results, next iteration
- [docs/AI_COLLABORATION_NOTE.md](docs/AI_COLLABORATION_NOTE.md) -- how AI was used to build this
- [docs/USER_GUIDE.md](docs/USER_GUIDE.md) -- for the person reviewing contracts day-to-day
- [docs/RUNBOOK.md](docs/RUNBOOK.md) -- operator guide: running it, maintaining the playbook, troubleshooting
- [docs/SPRINT_SELF_ASSESSMENT.md](docs/SPRINT_SELF_ASSESSMENT.md) -- honest scoring against the sprint brief, gaps included
- [backend/README.md](backend/README.md) -- backend-specific dev notes

## Non-goals (v1)

Not a substitute for a lawyer's sign-off on high-value/high-risk deals; no
legal advice; English-language contracts only; no multi-party or
amendment/redline-diffing support; no CLM/e-signature integration. See
docs/CASE_STUDY.md for the full scope discussion and next-iteration plan.
