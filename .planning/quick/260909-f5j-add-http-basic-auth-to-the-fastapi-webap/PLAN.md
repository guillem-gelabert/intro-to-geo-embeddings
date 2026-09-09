---
quick_id: 260909-f5j
date: 2026-09-09
description: Add HTTP basic auth to the FastAPI webapp, push to a new public GitHub repo, connect Railway web service to it
---

# Quick Task: basic auth + GitHub origin + Railway GitHub source

## Context

`webapp/` is served on Railway (project `geo-embeddings-course`, service `web`,
`web-production-0b234.up.railway.app`) and was deployed with `railway up` from the
working directory — the service has no source repo attached. The repo has no git
remote. The course material is a paid product, so the hosted companion needs a gate;
the user chose a **public** GitHub repo, so credentials live only in Railway
variables and never in the tree.

## Tasks

### 1. Basic auth in `webapp/app.py`

- Read `WEB_BASIC_AUTH_USER` / `WEB_BASIC_AUTH_PASSWORD` from the environment per
  request. Both unset → auth disabled (local `make web-serve` and the test suite
  keep working unchanged).
- HTTP middleware, so `/static` and every route is covered, not just the API.
- `/health` is exempt: Railway's healthcheck sends no `Authorization` header, and a
  401 there fails every deploy.
- `secrets.compare_digest` on user and password, both compared every time (no
  early return that would leak which half was wrong).
- 401 carries `WWW-Authenticate: Basic realm="..."` so browsers prompt.

### 2. Test coverage in `tests/test_web_course.py`

- Auth off when unset (existing behaviour holds).
- 401 without credentials, 401 on a wrong password, 200 with the right pair.
- `/health` reachable unauthenticated while auth is on.

### 3. Public GitHub repo + push

- `gh repo create guillem-gelabert/intro-to-geo-embeddings --public --source=. --push`.
- Confirm `data/raw/` and `.env*` stay ignored before the push (14 MB tracked, fine).

### 4. Railway service source

- Connect service `web` to the GitHub repo (`connect-service-source`), so pushes to
  `main` deploy instead of `railway up`.
- Set `WEB_BASIC_AUTH_USER` / `WEB_BASIC_AUTH_PASSWORD` as Railway variables with a
  generated password; report them to the user, never commit them.

## Out of scope

Rotating credentials, per-student accounts, or any auth beyond a single shared pair.
