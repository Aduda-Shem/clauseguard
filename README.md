# ClauseGuard

ClauseGuard is a contract review tool for small teams without in-house legal support.

Upload a contract and ClauseGuard checks it for common risks, explains the issue, and suggests whether to **sign, negotiate, or escalate**.

## What it checks

ClauseGuard uses a fixed rule-based playbook covering:

- Auto-renewal and notice periods
- Liability and indemnification
- Payment terms
- IP ownership and confidentiality
- Data privacy
- Assignment
- Governing law
- Non-compete clauses

Each finding includes:

- Risk level: Low, Medium, High, or Critical
- The relevant contract text
- Why it was flagged
- Recommended next action
- Suggested redline for Medium+ risks

You can also ask questions about the contract using plain English.

## How it works

```text
Upload contract
      ↓
Extract text
      ↓
Run risk rules
      ↓
Generate findings
      ↓
Save results
      ↓
Review and decide
```

Risk detection is **rule-based**, so the same contract produces consistent results.

Gemini is only used for generating redlines and answering contract questions. If Gemini is unavailable, the system falls back to templates.

## Tech Stack

- **Frontend:** React
- **Backend:** Django
- **Database:** PostgreSQL
- **AI:** Gemini
- **Deployment:** Docker + Nginx

## Running Locally

```bash
git clone https://github.com/Aduda-Shem/clauseguard.git
cd clauseguard

cp backend/.env.example backend/.env

docker-compose up
```

Open:

```text
http://localhost:5174
```

A `GEMINI_API_KEY` is optional. Without it, risk detection still works using the rule engine, while redlines and chat use fallback templates.

## Important Note

ClauseGuard is a **first-pass contract review tool**, not a replacement for legal advice. The final decision should always be made by a qualified person when needed.
