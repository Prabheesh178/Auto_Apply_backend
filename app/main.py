from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, AsyncSessionLocal
from app.api import api_router
from app.utils.seed_data import initialize_seed_data
from app.config import settings

from app.services.keep_alive import keep_alive_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Populate seed data if empty
    async with AsyncSessionLocal() as session:
        await initialize_seed_data(session)

    # Start automated anti-sleep keep-alive pinger
    keep_alive_service.start()

    yield

    # Cleanup
    keep_alive_service.stop()
    await engine.dispose()

app = FastAPI(
    title="Auto-Apply Backend API",
    description="Autonomous Internship Application System with Gemini & Playwright",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {
        "name": "Auto-Apply Agent API",
        "status": "online",
        "docs": "/docs",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
