"""
Run session routes — create session, upload video, trigger analysis, poll status.
"""
import asyncio
import os
import shutil
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.db_models import RunSession
from app.models.schemas import RunCreate, RunResponse, RunStatusResponse
from app.services.analysis_service import run_analysis

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = "data/uploads"
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
MAX_FILE_SIZE_MB = 500


@router.post("/runs", response_model=RunResponse, status_code=201)
async def create_run(body: RunCreate, db: AsyncSession = Depends(get_db)):
    session = RunSession(
        runner_id=body.runner_id,
        distance_type=body.distance_type,
        environment=body.environment,
        session_goal=body.session_goal,
        status="pending",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return RunResponse.model_validate(session)


@router.post("/runs/{run_id}/video")
async def upload_video(run_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RunSession).where(RunSession.id == run_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Run session not found")

    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported video format '{ext}'. Supported: {', '.join(ALLOWED_EXTENSIONS)}")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_name = f"session_{run_id}_{uuid.uuid4().hex[:8]}{ext}"
    dest = os.path.join(UPLOAD_DIR, unique_name)

    try:
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(500, f"File save failed: {e}")

    file_size_mb = os.path.getsize(dest) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        os.remove(dest)
        raise HTTPException(413, f"File too large ({file_size_mb:.0f} MB). Max {MAX_FILE_SIZE_MB} MB.")

    session.video_filename = unique_name
    session.status = "uploaded"
    await db.commit()
    return {"message": "Video uploaded", "filename": unique_name, "size_mb": round(file_size_mb, 2)}


@router.post("/runs/{run_id}/analyze")
async def start_analysis(run_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RunSession).where(RunSession.id == run_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Run session not found")
    if not session.video_filename:
        raise HTTPException(400, "No video uploaded for this session")
    if session.status == "processing":
        raise HTTPException(409, "Analysis is already in progress")

    # Kick off background analysis
    background_tasks.add_task(_run_analysis_task, run_id)
    session.status = "processing"
    session.processing_progress = 0.0
    session.processing_stage = "Queued…"
    await db.commit()
    return {"message": "Analysis started", "run_id": run_id}


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RunSession).where(RunSession.id == run_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Run session not found")
    return RunResponse.model_validate(session)


@router.get("/runs/{run_id}/status", response_model=RunStatusResponse)
async def get_run_status(run_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RunSession).where(RunSession.id == run_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Run session not found")
    return RunStatusResponse(
        id=session.id,
        status=session.status,
        processing_stage=session.processing_stage,
        processing_progress=session.processing_progress,
        error_message=session.error_message,
    )


@router.get("/runner/{runner_id}/runs")
async def list_runner_runs(runner_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RunSession)
        .where(RunSession.runner_id == runner_id)
        .order_by(RunSession.created_at.desc())
    )
    sessions = result.scalars().all()
    return [RunResponse.model_validate(s) for s in sessions]


async def _run_analysis_task(run_id: int):
    """Background task wrapper — gets its own DB session."""
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            await run_analysis(run_id, db)
        except Exception as e:
            logger.exception(f"Background analysis failed for run {run_id}: {e}")
