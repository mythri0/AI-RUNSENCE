"""
Analysis result routes — metrics, mistakes, timeline, coach, video streaming.
"""
import os
import re
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.db_models import RunSession

router = APIRouter()
PROCESSED_DIR = "data/processed"
UPLOAD_DIR = "data/uploads"


def _get_done_session(session: RunSession) -> RunSession:
    if not session:
        raise HTTPException(404, "Run session not found")
    if session.status not in ("done", "processing"):
        raise HTTPException(409, f"Analysis not complete (status: {session.status})")
    return session


@router.get("/runs/{run_id}/metrics")
async def get_metrics(run_id: int, db: AsyncSession = Depends(get_db)):
    session = await _fetch(run_id, db)
    _get_done_session(session)
    return {"run_id": run_id, **session.get_metrics()}


@router.get("/runs/{run_id}/mistakes")
async def get_mistakes(run_id: int, db: AsyncSession = Depends(get_db)):
    session = await _fetch(run_id, db)
    _get_done_session(session)
    return {"run_id": run_id, "mistakes": session.get_mistakes()}


@router.get("/runs/{run_id}/timeline")
async def get_timeline(run_id: int, db: AsyncSession = Depends(get_db)):
    session = await _fetch(run_id, db)
    _get_done_session(session)
    return {"run_id": run_id, "points": session.get_timeline(),
            "degradation_onset_s": session.get_fatigue().get("onset_time_s")}


@router.get("/runs/{run_id}/coach")
async def get_coach(run_id: int, db: AsyncSession = Depends(get_db)):
    session = await _fetch(run_id, db)
    _get_done_session(session)
    return {"run_id": run_id, **session.get_coach()}


@router.get("/runs/{run_id}/style")
async def get_style(run_id: int, db: AsyncSession = Depends(get_db)):
    session = await _fetch(run_id, db)
    _get_done_session(session)
    return {"run_id": run_id, **session.get_style()}


@router.get("/runs/{run_id}/priorities")
async def get_priorities(run_id: int, db: AsyncSession = Depends(get_db)):
    session = await _fetch(run_id, db)
    _get_done_session(session)
    return {"run_id": run_id, "priorities": session.get_priorities()}


@router.get("/runs/{run_id}/fatigue")
async def get_fatigue(run_id: int, db: AsyncSession = Depends(get_db)):
    session = await _fetch(run_id, db)
    _get_done_session(session)
    return {"run_id": run_id, **session.get_fatigue()}


@router.get("/runs/{run_id}/loading")
async def get_loading(run_id: int, db: AsyncSession = Depends(get_db)):
    session = await _fetch(run_id, db)
    _get_done_session(session)
    return {"run_id": run_id, **session.get_loading_index()}


@router.get("/runs/{run_id}/efficiency")
async def get_efficiency(run_id: int, db: AsyncSession = Depends(get_db)):
    session = await _fetch(run_id, db)
    _get_done_session(session)
    return {"run_id": run_id, **session.get_efficiency()}


@router.get("/runs/{run_id}/gait-cycles")
async def get_gait_cycles(run_id: int, db: AsyncSession = Depends(get_db)):
    session = await _fetch(run_id, db)
    _get_done_session(session)
    return {"run_id": run_id, "cycles": session.get_gait_cycles()}


import mimetypes

@router.get("/runs/{run_id}/video")
@router.get("/runs/{run_id}/video/{mode}")
async def get_video(run_id: int, request: Request, mode: str = "original", db: AsyncSession = Depends(get_db)):
    """
    Serve video file with proper HTTP range request support for browser playback.
    mode: original | pose | analysis
    """
    session = await _fetch(run_id, db)
    if not session:
        raise HTTPException(404, "Run session not found")

    orig_path = os.path.join(UPLOAD_DIR, session.video_filename or "")
    if mode == "original":
        path = orig_path
    elif mode == "pose":
        path = os.path.join(PROCESSED_DIR, f"session_{run_id}_pose.mp4")
        if not os.path.exists(path) or os.path.getsize(path) < 1000:
            path = orig_path
    elif mode == "analysis":
        path = os.path.join(PROCESSED_DIR, f"session_{run_id}_analysis.mp4")
        if not os.path.exists(path) or os.path.getsize(path) < 1000:
            path = orig_path
    else:
        raise HTTPException(400, "mode must be: original | pose | analysis")

    if not os.path.exists(path):
        raise HTTPException(404, f"Video file not found for mode '{mode}'")

    file_size = os.path.getsize(path)
    mime_type = mimetypes.guess_type(path)[0] or "video/mp4"
    range_header = request.headers.get("range")

    CHUNK = 1024 * 1024  # 1 MB chunks

    if range_header:
        match = re.search(r"bytes=(\d+)-(\d*)", range_header)
        if not match:
            raise HTTPException(416, "Invalid Range header")
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else min(start + CHUNK - 1, file_size - 1)
        end = min(end, file_size - 1)
        length = end - start + 1

        def iter_file():
            with open(path, "rb") as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    data = f.read(min(CHUNK, remaining))
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
            "Content-Type": mime_type,
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Range",
            "Access-Control-Expose-Headers": "Content-Range, Content-Length, Accept-Ranges",
            "Cache-Control": "no-cache",
        }
        return StreamingResponse(iter_file(), status_code=206, headers=headers)

    # Full file
    def iter_full():
        with open(path, "rb") as f:
            while chunk := f.read(CHUNK):
                yield chunk

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Type": mime_type,
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Range",
        "Access-Control-Expose-Headers": "Content-Range, Content-Length, Accept-Ranges",
        "Cache-Control": "no-cache",
    }
    return StreamingResponse(iter_full(), status_code=200, headers=headers)



@router.get("/runs/{run_id}/full")
async def get_full_analysis(run_id: int, db: AsyncSession = Depends(get_db)):
    """Return all analysis data in a single response for the frontend dashboard."""
    session = await _fetch(run_id, db)
    if not session:
        raise HTTPException(404, "Run session not found")

    return {
        "run_id": run_id,
        "status": session.status,
        "processing_stage": session.processing_stage,
        "processing_progress": session.processing_progress,
        "error_message": session.error_message,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "video_duration_s": session.video_duration_s,
        "video_fps": session.video_fps,
        "distance_type": session.distance_type,
        "environment": session.environment,
        "session_goal": session.session_goal,
        "metrics": session.get_metrics(),
        "baseline": session.get_baseline(),
        "mistakes": session.get_mistakes(),
        "fatigue": session.get_fatigue(),
        "style": session.get_style(),
        "priorities": session.get_priorities(),
        "coach": session.get_coach(),
        "timeline": session.get_timeline(),
        "loading_index": session.get_loading_index(),
        "efficiency": session.get_efficiency(),
        "gait_cycles": session.get_gait_cycles(),
    }


async def _fetch(run_id: int, db: AsyncSession):
    result = await db.execute(select(RunSession).where(RunSession.id == run_id))
    return result.scalar_one_or_none()
