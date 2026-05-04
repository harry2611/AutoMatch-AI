from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.cache import read_json
from app.core.security import require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.schemas.domain import AnalyticsOverviewResponse
from app.services.analytics import analytics_overview

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])

_CACHE_KEY = "analytics:overview"


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def overview(
    top_k: int = 5,
    _: object = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> AnalyticsOverviewResponse:
    """Return marketplace analytics, served from the Redis snapshot when available.

    The APScheduler job ``cache_analytics_snapshot`` refreshes the snapshot
    every 10 minutes.  On a cache miss (cold start, Redis down, or top_k ≠ 5)
    the response is computed live and the result is written back to the cache.
    """
    # Only serve cached result when using the default top_k so that custom
    # values always get a fresh computation.
    if top_k == 5:
        cached = read_json(_CACHE_KEY)
        if cached is not None:
            logger.debug("analytics:overview served from Redis cache")
            return AnalyticsOverviewResponse.model_validate(cached)

    logger.info("analytics:overview computed live (top_k=%d)", top_k)
    return analytics_overview(db, top_k=top_k)
