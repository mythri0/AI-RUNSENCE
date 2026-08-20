"""
Profile routes — create and retrieve runner profiles.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.db_models import Runner
from app.models.schemas import RunnerCreate, RunnerResponse

router = APIRouter()


@router.post("/profile", response_model=RunnerResponse, status_code=201)
async def create_profile(body: RunnerCreate, db: AsyncSession = Depends(get_db)):
    runner = Runner(**body.model_dump(exclude_none=True))
    db.add(runner)
    await db.commit()
    await db.refresh(runner)
    return _to_response(runner)


@router.get("/profile/{runner_id}", response_model=RunnerResponse)
async def get_profile(runner_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Runner).where(Runner.id == runner_id))
    runner = result.scalar_one_or_none()
    if not runner:
        raise HTTPException(404, "Runner not found")
    return _to_response(runner)


@router.put("/profile/{runner_id}", response_model=RunnerResponse)
async def update_profile(runner_id: int, body: RunnerCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Runner).where(Runner.id == runner_id))
    runner = result.scalar_one_or_none()
    if not runner:
        raise HTTPException(404, "Runner not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(runner, k, v)
    await db.commit()
    await db.refresh(runner)
    return _to_response(runner)


def _to_response(runner: Runner) -> RunnerResponse:
    return RunnerResponse(
        id=runner.id,
        name=runner.name,
        age=runner.age,
        weight_kg=runner.weight_kg,
        height_cm=runner.height_cm,
        gender=runner.gender,
        experience_level=runner.experience_level,
        primary_goal=runner.primary_goal,
        bmi=runner.bmi,
        created_at=runner.created_at,
    )
