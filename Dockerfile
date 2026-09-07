# The image serves the prebuilt bundle only: no notebooks, no geo stack, no data/raw.
# Rebuild the bundle with `make web-content` and commit it before deploying.
FROM ghcr.io/astral-sh/uv:0.12.9-python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    PYTHONUNBUFFERED=1

# Only the web extra -- rasterio, geopandas and friends are build-time tools here.
RUN uv pip install --system --no-cache \
      "fastapi>=0.121.0" "uvicorn>=0.40.0" "markdown-it-py>=4.0.0"

COPY webapp/ ./webapp/

EXPOSE 8000
CMD ["sh", "-c", "uvicorn webapp.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
