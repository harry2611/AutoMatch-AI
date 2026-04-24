from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import get_session
from app.services.analytics import cache_analytics_snapshot, refresh_dealer_quality_scores
from app.services.bayesian import recompute_priors_from_history


def _run_job(job_fn) -> None:
    db = get_session()
    try:
        job_fn(db)
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="America/Los_Angeles")
    scheduler.add_job(lambda: _run_job(recompute_priors_from_history), "interval", minutes=15, id="recompute-priors")
    scheduler.add_job(lambda: _run_job(refresh_dealer_quality_scores), "interval", minutes=20, id="dealer-quality")
    scheduler.add_job(lambda: _run_job(cache_analytics_snapshot), "interval", minutes=10, id="analytics-cache")
    scheduler.start()
    return scheduler


def stop_scheduler(scheduler: BackgroundScheduler) -> None:
    scheduler.shutdown(wait=False)

