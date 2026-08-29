# PostgreSQL deployment path

SQLite remains the default for local/single-instance use. Set `SEVAA_DATABASE_URL` to a `postgresql://` or `postgres://` URL to run the hardened runtime on PostgreSQL.

## Docker Compose

Use the base Compose file plus the PostgreSQL overlay:

```bash
export SEVAA_POSTGRES_PASSWORD='set-from-a-secret-store'
export SEVAA_FOUNDER_TOKEN='set-from-a-secret-store'
export SEVAA_AUTOMATION_TOKEN='set-from-a-secret-store'
docker compose -f compose.yaml -f compose.postgres.yaml up --build
```

Optional non-secret names:

```bash
export SEVAA_POSTGRES_USER=sevaa
export SEVAA_POSTGRES_DB=sevaa
```

The overlay waits for PostgreSQL health before starting the application. No production password is stored in the repository.

## Managed PostgreSQL

For a managed database, configure only the application service with the provider-issued URL:

```bash
SEVAA_DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
```

Keep TLS requirements from the provider in that URL/query string where required. Do not commit the URL because it normally contains credentials.

## Compatibility boundary

The current adapter intentionally supports the SQL subset already used by SEVAA Sales OS:

- `?` parameters are translated to psycopg placeholders.
- migration `INTEGER PRIMARY KEY AUTOINCREMENT` is translated to PostgreSQL `SERIAL PRIMARY KEY`.
- PostgreSQL rows preserve both mapping access (`row["id"]`) and the small amount of SQLite-style integer indexing used by the migration ledger.
- `lastrowid` is backed by PostgreSQL `LASTVAL()` for the existing immediate-after-insert call sites.

This is deliberately smaller than an ORM migration and keeps the SQLite path unchanged.

## Verification

`.github/workflows/sevaa-postgres.yml` launches a real PostgreSQL 17 service and runs `tests/test_postgres_runtime.py`. The integration covers migrations v1-v4 and the hardened flow from idempotent lead ingestion through proposal creation, founder approval enforcement, artifact/follow-up creation, secure share generation, and audited won outcome.

No external payment call or autonomous outbound message occurs in this test.
