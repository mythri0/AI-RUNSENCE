"""
Pydantic schemas for request/response validation.
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ─── Runner Profile ──────────────────────────────────────────────────────────

class RunnerCreate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=5, le=120)
    weight_kg: Optional[float] = Field(None, gt=0, le=500)
    height_cm: Optional[float] = Field(None, gt=0, le=300)
    gender: Optional[str] = None
    experience_level: Optional[str] = None   # beginner/intermediate/advanced/elite
    primary_goal: Optional[str] = None


class RunnerResponse(RunnerCreate):
    id: int
    bmi: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Run Session ─────────────────────────────────────────────────────────────

class RunCreate(BaseModel):
    runner_id: int
    distance_type: Optional[str] = None
    environment: Optional[str] = None
    session_goal: Optional[str] = None


class RunResponse(BaseModel):
    id: int
    runner_id: int
    created_at: datetime
    status: str
    processing_stage: Optional[str] = None
    processing_progress: float = 0.0
    error_message: Optional[str] = None
    distance_type: Optional[str] = None
    environment: Optional[str] = None
    session_goal: Optional[str] = None
    video_duration_s: Optional[float] = None
    video_fps: Optional[float] = None

    class Config:
        from_attributes = True


class RunStatusResponse(BaseModel):
    id: int
    status: str
    processing_stage: Optional[str] = None
    processing_progress: float = 0.0
    error_message: Optional[str] = None


# ─── Analysis Results ─────────────────────────────────────────────────────────

class MetricValue(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None
    label: str
    estimated: bool = True
    confidence: Optional[float] = None   # 0–1
    baseline: Optional[float] = None
    deviation_pct: Optional[float] = None
    note: Optional[str] = None


class MetricsResponse(BaseModel):
    run_id: int
    cadence: Optional[MetricValue] = None
    stride_normalized: Optional[MetricValue] = None
    vertical_oscillation: Optional[MetricValue] = None
    symmetry_index: Optional[MetricValue] = None
    trunk_lean: Optional[MetricValue] = None
    knee_angle_left: Optional[MetricValue] = None
    knee_angle_right: Optional[MetricValue] = None
    arm_swing: Optional[MetricValue] = None
    ground_contact_estimate: Optional[MetricValue] = None
    foot_strike: Optional[Dict[str, Any]] = None
    pelvic_stability: Optional[MetricValue] = None
    rhythm_score: Optional[MetricValue] = None
    window_data: Optional[List[Dict[str, Any]]] = None   # per-window time series


class MistakeEntry(BaseModel):
    id: str
    name: str
    severity: str        # low/medium/high
    confidence: float    # 0–1
    evidence: str
    timestamp_s: Optional[float] = None
    frame_number: Optional[int] = None
    relevant_metrics: Dict[str, Any] = {}
    possible_effect: str
    suggested_correction: str


class MistakesResponse(BaseModel):
    run_id: int
    mistakes: List[MistakeEntry]


class TimelinePoint(BaseModel):
    time_pct: float        # 0–100
    timestamp_s: float
    form_quality: str      # good/fair/poor/degrading
    color: str             # green/yellow/orange/red
    notes: List[str] = []


class TimelineResponse(BaseModel):
    run_id: int
    points: List[TimelinePoint]
    degradation_onset_s: Optional[float] = None


class CoachResponse(BaseModel):
    run_id: int
    doing_well: List[str]
    what_changed: List[str]
    why_it_matters: List[str]
    top_priority: str
    focus_next: List[str]
    context_recommendation: str
    generated_by: str   # "gemini" or "deterministic"


class EvolutionSession(BaseModel):
    session_id: int
    date: datetime
    efficiency_score: Optional[float] = None
    cadence_mean: Optional[float] = None
    symmetry_mean: Optional[float] = None
    posture_score: Optional[float] = None
    vertical_oscillation: Optional[float] = None
    trunk_lean: Optional[float] = None
    pelvic_stability: Optional[float] = None
    fatigue_detected: bool = False
    issues_count: int = 0
    primary_style: Optional[str] = None
    distance_type: Optional[str] = None


class EvolutionResponse(BaseModel):
    runner_id: int
    sessions: List[EvolutionSession]
    has_data: bool
