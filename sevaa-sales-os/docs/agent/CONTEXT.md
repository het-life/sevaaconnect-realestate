# Compact Product Context

Product: self-serve B2B SaaS for construction-sector businesses.
Human-by-exception target: automate lead qualification, proposal drafting, follow-up and pipeline management.

Architecture: Next.js-style dashboard + FastAPI API + PostgreSQL + optional Redis/worker. OpenClaw is orchestration only, not database of record.

Core safety:
- organization-scoped data
- audit every meaningful action
- structured/schema-validated AI outputs
- no secrets in Git
- no unsolicited bulk messaging
- approval required for price overrides, large discounts, contractual commitments, public claims, destructive data actions

MVP screens:
- Overview
- Pipeline
- Lead detail
- Proposal review
- Follow-ups
- Settings
- System health

MVP API targets:
POST /api/v1/leads
GET /api/v1/leads
POST /api/v1/leads/{id}/qualify
POST /api/v1/leads/{id}/score
GET /api/v1/pipeline
GET /api/v1/internal/daily-brief
