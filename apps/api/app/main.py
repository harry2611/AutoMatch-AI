from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.db.init_db import init_db
from app.jobs.scheduler import start_scheduler, stop_scheduler
from app.services.seed import seed_demo_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if settings.seed_demo_data:
        seed_demo_data()

    scheduler = start_scheduler() if settings.scheduler_enabled else None
    yield
    if scheduler is not None:
        stop_scheduler(scheduler)


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Bayesian buyer-to-vehicle marketplace optimization API with real-time posterior updates, "
        "dealer intelligence, and A/B analytics."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

