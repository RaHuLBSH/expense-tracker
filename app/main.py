from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db, settings
from app.routes.expenses import router as expenses_router
from app.routes.ui import router as ui_router
from contextlib import asynccontextmanager


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def create_app() -> FastAPI:
    configure_logging()
    log = logging.getLogger(__name__)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        init_db()
        log.info("startup complete")
        yield
        # Shutdown (optional)

    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(expenses_router)
    app.include_router(ui_router)

    return app


app = create_app()

