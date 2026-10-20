"""Application configuration.

All paths are relative to the ``backend/data`` directory by default, which is
the directory mounted as a Docker volume in production so the SQLite
database and uploaded images survive container restarts.
"""
from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DECK_DATA_DIR", BACKEND_DIR / "data"))
UPLOADS_DIR = DATA_DIR / "uploads"
OVERLAYS_CACHE_DIR = DATA_DIR / "overlays"
DB_PATH = DATA_DIR / "deck.db"

DEFAULT_DESCRIPTIONS_PATH = Path(
    os.environ.get(
        "DECK_DEFAULT_DESCRIPTIONS",
        BACKEND_DIR.parent / "default_description.md",
    )
)

# Directory containing the built frontend (Vite `dist/`), served as static
# files in production. Not required in development (the Vite dev server
# handles the frontend then).
FRONTEND_DIST_DIR = Path(
    os.environ.get("DECK_FRONTEND_DIST", BACKEND_DIR.parent / "frontend" / "dist")
)

MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB per image

for directory in (DATA_DIR, UPLOADS_DIR, OVERLAYS_CACHE_DIR):
    directory.mkdir(parents=True, exist_ok=True)
