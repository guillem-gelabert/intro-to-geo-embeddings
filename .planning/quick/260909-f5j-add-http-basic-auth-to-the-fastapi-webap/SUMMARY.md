---
quick_id: 260909-f5j
date: 2026-09-09
status: complete
---

# Summary: basic auth + GitHub origin + Railway GitHub source

## What shipped

- `webapp/app.py` grew an HTTP middleware gate driven by `WEB_BASIC_AUTH_USER` /
  `WEB_BASIC_AUTH_PASSWORD`. Both unset → no gate, so `make web-serve` and the tests
  are unchanged. `secrets.compare_digest` on both halves, always both, so a 401 never
  says which one was wrong. `/health` is exempt because Railway's probe sends no
  `Authorization` header.
- Four tests in `tests/test_web_course.py` cover: gate off when unconfigured, 401
  anonymous with a `WWW-Authenticate` challenge, 401 on a wrong password and on a
  wrong username, 200 with the right pair, and `/health` open while the gate is on.
- Repo pushed to https://github.com/guillem-gelabert/intro-to-geo-embeddings (public,
  as chosen). `.gitignore` gained `!.planning/quick/**/PLAN.md` — the author's global
  ignore has a `*plan.md` rule and the existing re-include only covered `*-PLAN.md`.
- Railway service `web` (project `geo-embeddings-course`) now builds from
  `guillem-gelabert/intro-to-geo-embeddings@main` instead of `railway up`, with the
  two auth variables set in the production environment.

## Verified

`uv run python -m pytest tests/` → 204 passed, 3 skipped. Live against
`web-production-0b234.up.railway.app` after the GitHub-triggered deploy: `/` 401
anonymous, 401 with a wrong password, 200 with the pair; `/api/index` 200
authenticated; `/health` 200 unauthenticated.

## Notes

- Credentials live only in Railway variables. The repo is public — never commit them.
- `.railwayignore` is now dead weight for normal deploys (GitHub builds use
  `.gitignore` + `.dockerignore`); it still applies if anyone falls back to
  `railway up`. Left in place.
- Pre-existing ruff findings (6 errors, 7 files unformatted) are unchanged by this
  task — the repo's committed state already differs from a bare `ruff` run.
