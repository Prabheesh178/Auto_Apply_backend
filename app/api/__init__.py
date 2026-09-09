from fastapi import APIRouter
from app.api.candidate import router as candidate_router
from app.api.settings import router as settings_router
from app.api.jobs import router as jobs_router
from app.api.applications import router as applications_router
from app.api.analytics import router as analytics_router
from app.api.stream import router as stream_router
from app.api.watcher import router as watcher_router

api_router = APIRouter(prefix="/api")
api_router.include_router(candidate_router)
api_router.include_router(settings_router)
api_router.include_router(jobs_router)
api_router.include_router(applications_router)
api_router.include_router(analytics_router)
api_router.include_router(stream_router)
api_router.include_router(watcher_router)
