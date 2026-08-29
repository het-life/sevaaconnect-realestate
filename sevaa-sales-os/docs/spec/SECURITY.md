# Security and Autonomy Controls

## Principles

- least privilege
- organization isolation
- immutable audit trail where practical
- explicit approval boundaries
- secrets outside Git
- safe defaults
- rate limiting
- input validation
- dependency pinning
- backups

## Secret handling

Never commit:
- API keys
- OAuth secrets
- payment secrets
- database passwords
- OpenClaw tokens
- SMTP credentials

Provide `.env.example`.

## Approval classes

### AUTO
Allowed automatically:
- normalize lead
- deduplicate
- classify
- score
- generate draft
- schedule routine follow-up
- analytics
- reports

### APPROVAL_REQUIRED
- pricing override
- discount above configured threshold
- contractual commitment
- refund above configured threshold
- public claim
- destructive data action

### PROHIBITED
- plaintext password storage
- cross-tenant data access
- bypassing payment entitlements
- unrestricted money transfers
- autonomous legal signing
- mass spam

## Data retention

Make retention configurable.
Provide deletion/export mechanism later.
Avoid collecting sensitive personal data that is not needed.

## Messaging

Do not build unsolicited bulk outreach.
Follow-ups should apply to legitimate leads or opted-in contacts.

## Failure mode

If AI is unavailable:
- preserve the lead
- queue work
- show degraded state
- do not fabricate output

If billing is unavailable:
- do not silently grant permanent entitlement
- preserve existing customer access according to configured grace rules

If database is unavailable:
- fail closed for writes
