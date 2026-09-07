"""Mobile web companion for the geospatial-embeddings course.

Serves the prebuilt content bundle from `tools/build_web_course.py`. Nothing here
executes student code -- every result the reader sees was baked in at build time from
the executed solution notebooks.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = STATIC_DIR / "index.html"

app = FastAPI(title="Geospatial Embeddings — mobile course", docs_url=None, redoc_url=None)


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
