# Careerist QA Automation Internship — Reelly

This is the base automation repo for the internship tasks.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run tests
```bash
python -m behave -f pretty
```

## Repo structure
- `app/` — Application bootstrap
- `pages/` — Page Objects (POM)
- `features/tests/` — Behave feature files (BDD)
- `features/steps/` — Step definitions
- `features/environment.py` — Behave hooks (driver setup)
