# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.3
FROM python:${PYTHON_VERSION}-slim as builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/root/.cache/uv

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project --no-dev

FROM python:${PYTHON_VERSION}-slim as runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN adduser --disabled-password --gecos "" --home "/nonexistent" \
    --shell "/sbin/nologin" --no-create-home --uid 10001 appuser

COPY --from=builder /app/.venv /app/.venv
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000


# --chdir locallibrary: переходить в папку, де лежить manage.py
# --bind 0.0.0.0:8000: слухає всі інтерфейси всередині контейнера
# --workers 3: стандартна кількість паралельних процесів
# --timeout 120: щоб не було помилок "WORKER TIMEOUT"
# --max-requests 1000: перезапуск воркера після 1000 запитів
CMD ["gunicorn", \
     "--chdir", "locallibrary", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--max-requests", "1000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "locallibrary.wsgi:application"]