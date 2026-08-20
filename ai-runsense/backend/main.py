"""
AI RunSense — FastAPI Application Entry Point
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.database import init_db
from app.api.routes import profile, runs, analysis, evolution, auth

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("ai-runsense")

DATA_DIRS = ["data/uploads", "data/processed", "data/sessions"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    for d in DATA_DIRS:
        os.makedirs(d, exist_ok=True)
    await init_db()
    logger.info("AI RunSense backend ready.")
    yield
    # Shutdown
    logger.info("AI RunSense backend shutting down.")


app = FastAPI(
    title="AI RunSense",
    description="Intelligent Video-Based Running Analysis & Personalized Performance Coach",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(profile.router, prefix="/api", tags=["Profile"])
app.include_router(runs.router, prefix="/api", tags=["Runs"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(evolution.router, prefix="/api", tags=["Evolution"])

# Serve processed video/frame files
os.makedirs("data/processed", exist_ok=True)
app.mount("/data", StaticFiles(directory="data"), name="data")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "AI RunSense"}
