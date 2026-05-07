# Local DB Reset

Use one of the options below to clear all data and start fresh. After reset, the default admin user will be re-seeded automatically on the first login or registration request.

> Note: Resetting wipes everything — users, stores, products, sales, planograms (including version history), import logs, and the per-user planogram quota counter. The seeded admin (below) and tier-default plan limits will be re-created automatically; per-user `annual_planogram_limit_override` values are lost.

## Option A: Docker Compose (recommended)

```bash
# Stop containers and remove the Postgres volume
# WARNING: This deletes all data

docker compose down -v

docker compose up --build
```

## Option B: Local Postgres (no Docker)

```bash
# Replace the database name if you changed it
# WARNING: This deletes all data

dropdb eureka_db
createdb eureka_db

# Re-apply migrations
poetry run alembic upgrade head
```

## Default Admin (auto-seeded)

- Email: admin@aexiz.com
- Password: qwerty123

This account is created automatically when `/api/v1/auth/register` or `/api/v1/auth/login` is called on a fresh database.
