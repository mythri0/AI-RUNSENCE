"""
Runner Evolution routes — multi-session trend data.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.db_models import RunSession, Runner
from app.models.schemas import EvolutionResponse, EvolutionSession

router = APIRouter()


@router.get("/runner/{runner_id}/evolution", response_model=EvolutionResponse)
async def get_evolution(runner_id: int, db: AsyncSession = Depends(get_db)):
    # Verify runner exists
    r_result = await db.execute(select(Runner).where(Runner.id == runner_id))
    runner = r_result.scalar_one_or_none()
    if not runner:
        raise HTTPException(404, "Runner not found")

    # Fetch completed sessions ordered by date
    s_result = await db.execute(
        select(RunSession)
        .where(RunSession.runner_id == runner_id, RunSession.status == "done")
        .order_by(RunSession.created_at.asc())
    )
    sessions = s_result.scalars().all()

    ev_sessions = []
    for s in sessions:
        metrics = s.get_metrics()
        mistakes = s.get_mistakes()
        vo = metrics.get("vertical_oscillation", {}).get("value")
        trunk = metrics.get("trunk_lean", {}).get("value")
        pelvic = metrics.get("pelvic_stability", {}).get("value")

        ev_sessions.append(
            EvolutionSession(
                session_id=s.id,
                date=s.created_at,
                efficiency_score=s.efficiency_score,
                cadence_mean=s.cadence_mean,
                symmetry_mean=s.symmetry_mean,
                posture_score=s.posture_score,
                vertical_oscillation=vo,
                trunk_lean=trunk,
                pelvic_stability=pelvic,
                fatigue_detected=s.fatigue_detected or False,
                issues_count=len(mistakes),
                primary_style=s.primary_style,
                distance_type=s.distance_type,
            )
        )

    return EvolutionResponse(
        runner_id=runner_id,
        sessions=ev_sessions,
        has_data=len(ev_sessions) > 0,
    )
