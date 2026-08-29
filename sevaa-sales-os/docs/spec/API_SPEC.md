# Initial API Specification

Prefix: /api/v1

## Health
GET /health
GET /ready

## Auth
POST /auth/register
POST /auth/login
POST /auth/logout
GET /auth/me

## Organizations
POST /organizations
GET /organizations/current
PATCH /organizations/current

## Leads
POST /leads
GET /leads
GET /leads/{id}
PATCH /leads/{id}
POST /leads/{id}/qualify
POST /leads/{id}/score
POST /leads/{id}/summarize

## Proposals
POST /leads/{id}/proposals/draft
GET /proposals/{id}
POST /proposals/{id}/approve
POST /proposals/{id}/mark-sent

## Follow-ups
GET /followups
POST /leads/{id}/followups
POST /followups/{id}/complete
POST /followups/run-due

## Pipeline
GET /pipeline
GET /analytics/funnel
GET /analytics/summary

## Settings
GET /settings/business
PATCH /settings/business
GET /settings/products
POST /settings/products
PATCH /settings/products/{id}

## Billing
GET /billing/subscription
POST /billing/checkout-session
POST /billing/webhook

## Internal/OpenClaw
Use separate authenticated service credentials.

GET /internal/daily-brief
GET /internal/weekly-report
POST /internal/audits/stale-leads
POST /internal/jobs/run

Internal routes must never be public without auth.
