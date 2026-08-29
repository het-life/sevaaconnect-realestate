# OpenClaw Automation Plan

Implement only after application endpoints exist.

## Daily

### Morning brief
Call:
GET /api/v1/internal/daily-brief

Output:
- new leads
- high-score leads
- overdue follow-ups
- proposals awaiting approval
- pipeline value
- system failures

### Stale lead audit
POST /api/v1/internal/audits/stale-leads

### Due follow-ups
POST /api/v1/followups/run-due

Use safe messaging rules.
Initially create/send only according to configured approval mode.

## Weekly

### Funnel report
- leads
- qualified
- proposals
- wins
- losses
- conversion
- average response time
- pipeline

### Cost report
- model/API spend
- infrastructure estimate
- cost per qualified lead
- cost per proposal

### Reliability report
- failed jobs
- retries
- health incidents
- backup status

## Escalation

Notify founder only when:
- proposal requires non-standard approval
- high-value lead needs attention
- repeated job failure
- billing failure
- security anomaly
- system health failure
