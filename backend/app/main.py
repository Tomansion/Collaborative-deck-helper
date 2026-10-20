from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .database import SessionLocal
from .routers import cards, export, history, ws
from .seed import bootstrap

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        bootstrap(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Collaborative Deck Helper - Les Cinq Rois", lifespan=lifespan)

# In development the frontend runs on the Vite dev server (a different
# origin/port) and talks to this API directly, so CORS must be open for
# local dev hosts. In production the frontend is served by this same app
# (see the StaticFiles mount below), so CORS doesn't come into play there.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cards.router)
app.include_router(history.router)
app.include_router(export.router)
app.include_router(ws.router)

app.mount("/uploads", StaticFiles(directory=config.UPLOADS_DIR), name="uploads")

if config.FRONTEND_DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=config.FRONTEND_DIST_DIR / "assets"), name="frontend-assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        candidate = config.FRONTEND_DIST_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(config.FRONTEND_DIST_DIR / "index.html")
