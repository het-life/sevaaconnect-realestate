# OpenClaw Automation Contract

The hardened automation contract uses `/api/v2` only.

## Credential boundary

OpenClaw must use `SEVAA_AUTOMATION_TOKEN`, never the founder token.

Every request carries:

- `Authorization: Bearer <SEVAA_AUTOMATION_TOKEN>`
- `X-Actor: <stable automation actor name>`

Before any workflow, call `GET /api/v2/auth/me` and require `role == "automation"`.

The repository helper `scripts/openclaw_client.py` enforces this identity check and intentionally exposes **no founder approval-decision method**.

The backend independently enforces the same boundary: automation credentials receive HTTP 403 on founder-only approval decisions.

## Environment

```bash
export SEVAA_BASE_URL=http://127.0.0.1:8000
export SEVAA_AUTOMATION_TOKEN='set-in-secret-store-not-git'
```

Never store token values in Git, prompts, logs, state files, issue bodies, or generated artifacts.

## Safe client operations

### Identity

```bash
python scripts/openclaw_client.py me
```

### Daily brief

```bash
python scripts/openclaw_client.py brief
```

Calls `GET /api/v2/internal/daily-brief` and returns new/high-score leads, proposal approvals awaiting founder action, pending/overdue follow-ups, pipeline value, and founder-attention count.

### Inspect approval queue

```bash
python scripts/openclaw_client.py approvals --status pending
```

Read-only. OpenClaw may surface pending approvals but may not resolve them.

### Inspect follow-ups

```bash
python scripts/openclaw_client.py followups --state overdue
```

### Create a normalized lead

```bash
python scripts/openclaw_client.py create-lead \
  --idempotency-key source-event-123 \
  --json '{"name":"Buyer","requirement":"20ft modular office","source":"openclaw"}'
```

Use a stable upstream event ID as the idempotency key when available. Duplicate protection remains enabled.

### Create + submit a proposal draft

```bash
python scripts/openclaw_client.py create-proposal 42 --amount 725000 --scope '20ft modular office shell + interiors'
python scripts/openclaw_client.py submit-proposal 7
```

Submission creates a founder approval request. It does **not** authorize external transmission.

### Schedule follow-up work

```bash
python scripts/openclaw_client.py schedule-followup 42 \
  --due-at '2026-09-01T04:00:00+00:00' \
  --channel manual \
  --draft-message 'Review buyer response before any external send.'
```

Channels such as email/WhatsApp represent draft intent only. No autonomous sender is enabled.

### Complete a follow-up

```bash
python scripts/openclaw_client.py complete-followup 9 --note 'Reviewed internally'
```

Only mark complete when the underlying work actually occurred.

## Suggested unattended loop

1. Verify automation identity.
2. Read daily brief.
3. Inspect overdue follow-ups.
4. Create/schedule internal work that is safe and reversible.
5. Draft proposals when evidence is sufficient.
6. Submit proposal drafts into the founder approval queue.
7. Surface only exception-level founder attention.
8. Record failures without secrets.
9. Never resolve founder approvals, send external messages, spend money, create payment links, transfer funds, or enter contractual commitments.

## Escalate to founder only when

- a proposal is awaiting approval
- price/scope requires a business judgment
- a high-value lead needs a human decision
- repeated job failure occurs
- billing/payment verification fails
- a security anomaly appears
- health/deployment is degraded

## Future automation work

After deployment hardening, add scheduled stale-lead audits, funnel/cost/reliability reports, and founder-reviewed outbound drafts. Preserve the same least-authority boundary.
