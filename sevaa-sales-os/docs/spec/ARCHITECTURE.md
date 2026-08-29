# Architecture

## High-level

Browser / Lead Form / API
        |
        v
FastAPI Backend
        |
        +--> PostgreSQL
        |
        +--> Background Job Queue
        |
        +--> AI Provider Adapter
        |
        +--> Email/Message Adapter
        |
        +--> Billing Adapter
        |
        +--> Audit Log
        |
        v
Next.js Dashboard

OpenClaw operates as an orchestration/control layer around the application,
not as the database of record.

## Services

### API service
Owns:
- auth
- organizations
- leads
- proposals
- follow-ups
- usage
- billing entitlements
- audit events

### Worker
Owns:
- AI jobs
- follow-up scheduling
- reports
- retries
- integration events

### Frontend
Owns:
- onboarding
- lead inbox
- lead detail
- pipeline
- proposal review
- settings
- usage/billing
- admin/health view

## AI abstraction

Create interface:

AIProvider
- extract_lead()
- classify_lead()
- generate_qualification_questions()
- summarize_lead()
- draft_proposal()
- draft_followup()

All AI calls must:
- return structured data
- be schema validated
- record model/provider
- record latency
- record cost estimate
- support retries
- support a deterministic/mock provider in tests

## Multi-tenancy

Every business record must belong to organization_id.
All queries must enforce organization scope.
Add tests specifically for cross-tenant leakage.

## Auditability

Record:
- actor
- organization
- action
- object type
- object id
- before/after or metadata
- approval state
- timestamp

## OpenClaw integration

OpenClaw may:
- call internal admin/report endpoints
- trigger scheduled audits
- request summaries
- queue content/report jobs
- monitor health

OpenClaw must not:
- directly modify database tables
- bypass application permissions
- bypass billing entitlements
- bypass approval-required actions

## Deployment

Initial:
- one Linux host
- Docker Compose
- PostgreSQL
- Redis if needed
- API
- worker
- frontend
- reverse proxy
- backups

Scale later:
- managed DB
- independent workers
- object storage
- managed queue
- CDN
