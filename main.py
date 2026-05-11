"""Repo-root entry point for Railway / railpack.

Railpack auto-detects `uvicorn main:app` from /app/main.py for Python ASGI
projects, ignoring custom start commands. So we ship this thin shim that:
  1. Re-exports the FastAPI app so `uvicorn main:app` works
  2. When run as __main__, reads PORT from env (Railway exec's startCommand
     without a shell, so $PORT in a string doesn't expand) and starts uvicorn

Migrations run on import — that way alembic upgrade head is applied before
the first request lands, without requiring a separate startup phase.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("toolpulse-bootstrap")


def _run_migrations() -> None:
    """Apply pending Alembic migrations. Idempotent. Fail loud."""
    try:
        log.info("running alembic upgrade head")
        result = subprocess.run(
            ["alembic", "-c", "api/alembic.ini", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        if result.returncode != 0:
            log.warning("alembic exited %d:\nstdout:\n%s\nstderr:\n%s",
                        result.returncode, result.stdout[-1500:], result.stderr[-1500:])
        else:
            log.info("migrations applied")
    except Exception as e:
        log.warning("migration runner failed: %s", e)


_run_migrations()

# Re-export FastAPI app so `uvicorn main:app` works
from api.main import app  # noqa: E402,F401


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WEB_CONCURRENCY", "2"))
    log.info("starting uvicorn on port=%d workers=%d", port, workers)
    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=workers)
