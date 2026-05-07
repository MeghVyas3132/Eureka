# Security

## Reporting

Found a vulnerability in Eureka? Please report it privately to the maintainer rather than opening a public issue. Include reproduction steps, affected component (backend / frontend / docker / infra), and your assessment of impact.

## In-scope

- Authentication or authorisation bypass
- Cross-tenant data leakage (see hard constraint: every query scoped by `user_id`)
- Injection attacks (SQL, command, header)
- Cross-site scripting via uploaded files or user-supplied store / product names
- Improper handling of file uploads (size, type, malicious payloads)
- Token leakage or insufficient JWT validation

## Out-of-scope

- Issues that require local network access without authentication assumptions
- Vulnerabilities in third-party dependencies that are already publicly known but not yet upgraded — file an issue/PR instead
- Findings on the dev `docker-compose.yml` (it ships dev defaults; production deploy is the responsibility of the operator, see [`docs/DEPLOY.md`](docs/DEPLOY.md))

## Defaults to be aware of

- The dev compose file sets a hard-coded Postgres password (`eureka`) and a placeholder `SECRET_KEY` if none is provided. Always supply a strong `SECRET_KEY` in `.env` before running anywhere reachable from the network.
- File uploads are size-capped at 10 MB and validated by content sniffing (`python-magic`), not by `Content-Type`. Files are archived to S3 (or local disk in dev) for audit.
- All write endpoints require a valid bearer token; admin endpoints require role `admin`.
