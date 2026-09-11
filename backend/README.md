# ClauseGuard backend

Django + Django REST Framework. This file is dev-workflow notes only.

## Local dev without Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env 
python manage.py migrate
python manage.py load_playbook
python manage.py runserver 0.0.0.0:8001
```

## Tests

```bash
python -m pytest -q
```

22 tests: clause-analyzer unit tests (rule evaluation, exclude-pattern
negation handling, malformed-regex safety), parsing tests (.txt/.docx/.pdf,
corrupted-file handling), and API integration tests.

## Evaluation harness

```bash
python eval/run_eval.py
```

Runs all 13 contracts in `eval/contracts/` through the real pipeline (same
code the API uses) and checks each against `eval/test_cases.json`. Results
written to `eval/results/results.json`.

## Maintaining the playbook

Playbook rules live in `reviews/fixtures/playbook_rules.json`, loaded into
the `PlaybookRule` table by `python manage.py load_playbook` (idempotent --
safe to re-run after editing the JSON).
