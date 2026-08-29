# SEVAA Sales OS

Runnable first milestone of the construction-sector lead-to-proposal operating system.

## What works
- Persistent SQLite database
- Lead creation API
- Deterministic lead scoring and auto-qualification
- Pipeline stages and stage transitions
- Audit log for every lead creation / stage transition
- Aggregated founder dashboard API
- iPhone-friendly dashboard backed by the real API
- Demo seed endpoint
- Tests for the primary lead lifecycle

## Run locally
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
./run.sh
```
Open `http://localhost:8000`.

API docs: `http://localhost:8000/docs`

## Tests
```bash
pytest -q
```

## Safety boundary
No autonomous public messaging, financial commitments, payments, live trading, or secret material is enabled. OpenClaw should orchestrate through the API and approval gates; SQLite is the local source of truth for this milestone.

## Low-token agent resume
Start with `docs/agent/BOOT.txt`, then `CURRENT.md` and only the files explicitly requested by the active TODO item.
