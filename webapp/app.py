"""Mobile web companion for the geospatial-embeddings course.

Serves the prebuilt content bundle from `tools/build_web_course.py`. Nothing here
executes student code -- every result the reader sees was baked in at build time from
the executed solution notebooks.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import secrets
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = STATIC_DIR / "index.html"

app = FastAPI(title="Geospatial Embeddings — mobile course", docs_url=None, redoc_url=None)

# Railway's healthcheck sends no Authorization header, so a gated /health fails
# every deploy.
UNGATED_PATHS = {"/health"}
AUTH_REALM = "Geospatial Embeddings course"


def credentials_from_env() -> tuple[str, str] | None:
    """The shared pair the reader must present, or None when the gate is off.

    Read per request rather than at import so the deployed service picks up a
    changed Railway variable on restart alone, and so tests can toggle it.
    """
    user = os.environ.get("WEB_BASIC_AUTH_USER", "")
    password = os.environ.get("WEB_BASIC_AUTH_PASSWORD", "")
    return (user, password) if user and password else None


def header_matches(header: str | None, expected: tuple[str, str]) -> bool:
    if not header or not header.lower().startswith("basic "):
        return False
    try:
        decoded = base64.b64decode(header[6:].strip(), validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return False
    user, _, password = decoded.partition(":")
    # Both halves are always compared: an early return on the username would
    # tell an attacker which one they got right.
    user_ok = secrets.compare_digest(user, expected[0])
    password_ok = secrets.compare_digest(password, expected[1])
    return user_ok and password_ok


@app.middleware("http")
async def basic_auth(request: Request, call_next):
    expected = credentials_from_env()
    if expected is None or request.url.path in UNGATED_PATHS:
        return await call_next(request)
    if header_matches(request.headers.get("authorization"), expected):
        return await call_next(request)
    return Response(
        status_code=401,
        headers={"WWW-Authenticate": f'Basic realm="{AUTH_REALM}"'},
    )


@lru_cache(maxsize=32)
def load_bundle(name: str) -> dict:
    path = CONTENT_DIR / f"{name}.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"no module {name!r}")
    return json.loads(path.read_text(encoding="utf-8"))


def known_slugs() -> set[str]:
    try:
        return {m["slug"] for m in load_bundle("index")["modules"]}
    except HTTPException:
        return set()


@app.get("/health")
def health() -> JSONResponse:
    modules = sorted(known_slugs())
    return JSONResponse({"status": "ok" if modules else "empty", "modules": len(modules)})


@app.get("/api/index")
def api_index() -> dict:
    return load_bundle("index")


@app.get("/api/module/{slug}")
def api_module(slug: str) -> dict:
    if slug not in known_slugs():
        raise HTTPException(status_code=404, detail=f"no module {slug!r}")
    return load_bundle(slug)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
@app.get("/m/{slug}")
def index_page(slug: str | None = None) -> FileResponse:
    return FileResponse(INDEX_HTML)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))


if __name__ == "__main__":
    main()
