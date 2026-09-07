# The image serves the prebuilt bundle only: no notebooks, no geo stack, no data/raw.
# Rebuild the bundle with `make web-content` and commit it before deploying.
FROM python:3.12-slim-bookworm

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Runtime is a strict subset of the `web` extra: markdown is rendered to HTML at
# bundle-build time, so markdown-it-py never ships. Versions match uv.lock.
RUN pip install --no-cache-dir "fastapi==0.141.1" "uvicorn==0.52.4"

COPY webapp/ ./webapp/

RUN useradd --create-home --uid 10001 app && chown -R app /app
USER app

EXPOSE 8000
CMD ["sh", "-c", "uvicorn webapp.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
