from fastapi import APIRouter

from app.api.routes.analytics import router as analytics_router
from app.api.routes.auth import router as auth_router
from app.api.routes.dealers import router as dealers_router
from app.api.routes.events import router as events_router
from app.api.routes.experiments import router as experiments_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.vehicles import router as vehicles_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(recommendations_router)
api_router.include_router(events_router)
api_router.include_router(dealers_router)
api_router.include_router(vehicles_router)
api_router.include_router(experiments_router)
api_router.include_router(analytics_router)

