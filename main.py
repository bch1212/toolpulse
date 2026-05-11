"""Repo-root entry point.

main.py:
  - Re-exports `app` so `uvicorn main:app` (and any worker fork) just imports the FastAPI app.
  - When run as __main__, runs migrations once in the parent then starts uvicorn.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("toolpulse-bootstrap")

# Re-export FastAPI app — pure import path, no side effects, safe across worker forks
from api.main import app  # noqa: E402,F401


def _run_migrations() -> None:
    try:
        log.info("running alembic upgrade head")
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", "api/alembic.ini", "upgrade", "head"],
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


if __name__ == "__main__":
    _run_migrations()
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WEB_CONCURRENCY", "1"))
    log.info("starting uvicorn on port=%d workers=%d", port, workers)
    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=workers)
