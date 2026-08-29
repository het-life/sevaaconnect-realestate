# Deployment Plan

## Development

Linux or macOS with Docker.

Services:
- postgres
- redis (if selected)
- api
- worker
- frontend

Command target:
docker compose up --build

## Initial production

One small Linux VPS is acceptable for early users.

Requirements:
- HTTPS
- firewall
- automatic security updates
- database backup
- application backup
- log rotation
- disk monitoring
- restart policy
- environment secrets
- health monitoring

## Backup

At minimum:
- nightly database dump
- encrypted/off-host copy
- retention policy
- documented restore test

## Scaling triggers

Move database to managed service when:
- customer count or data criticality justifies it
- restore/reliability burden becomes material

Split workers when:
- background jobs impact API latency

Do not prematurely introduce Kubernetes.
