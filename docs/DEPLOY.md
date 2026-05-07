# Deploy

For local dev see the root [`../readme.md`](../readme.md). This doc covers the deploy primitives.

## Local docker-compose stack

Three services in [`../docker-compose.yml`](../docker-compose.yml):

| Service | Image | Notes |
|---------|-------|-------|
| `postgres` | `postgres:16` | Persistent volume `pg_data`. Default credentials `eureka / eureka / eureka_db`. |
| `backend` | built from `backend/Dockerfile` | Runs `alembic upgrade head` then `uvicorn --reload`. Code mounted as a volume. |
| `frontend` | built from `frontend/Dockerfile` | Runs `npm run dev`. Code mounted; `node_modules` kept inside the container. |

```bash
make up         # bring up all three
make ps         # status
make logs       # tail backend + frontend
make down       # stop
make reset      # nuke Postgres volume + rebuild
```

## Required env

`.env` (copy from `.env.example`):

```
SECRET_KEY=<32+ char random string>          # required
DATABASE_URL=postgresql+asyncpg://eureka:eureka@postgres:5432/eureka_db
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
USE_LOCAL_STORAGE=true
LOCAL_UPLOAD_DIR=/app/uploads
CORS_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
ENVIRONMENT=development
```

For S3-backed uploads in non-dev:

```
USE_LOCAL_STORAGE=false
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
S3_BUCKET_NAME=eureka-uploads
```

## Migrations

Alembic auto-runs on backend boot. To run manually:

```bash
make backend-shell
poetry run alembic upgrade head
poetry run alembic current
```

Latest migration: `backend/alembic/versions/20260504_0012_align_planogram_defaults.py`.

## Health checks

- API live: `curl -fsS http://localhost:8000/openapi.json | head -c 200`
- Frontend live: `curl -fsSI http://localhost:3000/login | head -1`
- Postgres ready: `docker compose exec postgres pg_isready -U eureka`

## Rebuild after code changes

Backend code is mounted, so it hot-reloads via `uvicorn --reload`. Rebuild only when dependencies (`pyproject.toml`, `package.json`) change:

```bash
make rebuild
```

For frontend Next config changes (e.g. `next.config.js`), restart the container:

```bash
docker compose restart frontend
```

## Production notes

The current docker-compose targets local development. For production, replace the `command:` directives with a non-reload server (`uvicorn --workers N`, `next start`), pin image tags, terminate TLS upstream, and move secrets out of the file.
