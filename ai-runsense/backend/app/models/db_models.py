"""
SQLAlchemy ORM models for AI RunSense.
All tables are designed for SQLite; compatible with PostgreSQL via URL swap.
"""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base


class Runner(Base):
    __tablename__ = "runners"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    gender = Column(String(20), nullable=True)
    experience_level = Column(String(50), nullable=True)   # beginner/intermediate/advanced/elite
    primary_goal = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("RunSession", back_populates="runner", cascade="all, delete-orphan")

    @property
    def bmi(self):
        if self.weight_kg and self.height_cm and self.height_cm > 0:
            return round(self.weight_kg / ((self.height_cm / 100) ** 2), 1)
        return None


class RunSession(Base):
    __tablename__ = "run_sessions"

    id = Column(Integer, primary_key=True, index=True)
    runner_id = Column(Integer, ForeignKey("runners.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Context
    distance_type = Column(String(50), nullable=True)   # sprint/middle/long/marathon/ultra/general
    environment = Column(String(50), nullable=True)     # track/road/trail/treadmill/other
    session_goal = Column(String(100), nullable=True)

    # Video
    video_filename = Column(String(255), nullable=True)
    video_duration_s = Column(Float, nullable=True)
    video_fps = Column(Float, nullable=True)
    video_width = Column(Integer, nullable=True)
    video_height = Column(Integer, nullable=True)

    # Processing
    status = Column(String(30), default="pending")   # pending/processing/done/error
    processing_stage = Column(String(100), nullable=True)
    processing_progress = Column(Float, default=0.0)  # 0–100
    error_message = Column(Text, nullable=True)

    # Summary metrics (stored as JSON)
    metrics_json = Column(Text, nullable=True)
    baseline_json = Column(Text, nullable=True)
    mistakes_json = Column(Text, nullable=True)
    fatigue_json = Column(Text, nullable=True)
    style_json = Column(Text, nullable=True)
    priorities_json = Column(Text, nullable=True)
    coach_json = Column(Text, nullable=True)
    timeline_json = Column(Text, nullable=True)
    loading_index_json = Column(Text, nullable=True)
    efficiency_json = Column(Text, nullable=True)
    gait_cycles_json = Column(Text, nullable=True)

    # Aggregate scores for evolution tracking
    efficiency_score = Column(Float, nullable=True)
    cadence_mean = Column(Float, nullable=True)
    symmetry_mean = Column(Float, nullable=True)
    posture_score = Column(Float, nullable=True)
    fatigue_detected = Column(Boolean, default=False)
    primary_style = Column(String(100), nullable=True)

    runner = relationship("Runner", back_populates="sessions")

    def get_metrics(self):
        return json.loads(self.metrics_json) if self.metrics_json else {}

    def get_mistakes(self):
        return json.loads(self.mistakes_json) if self.mistakes_json else []

    def get_style(self):
        return json.loads(self.style_json) if self.style_json else {}

    def get_priorities(self):
        return json.loads(self.priorities_json) if self.priorities_json else []

    def get_coach(self):
        return json.loads(self.coach_json) if self.coach_json else {}

    def get_timeline(self):
        return json.loads(self.timeline_json) if self.timeline_json else []

    def get_loading_index(self):
        return json.loads(self.loading_index_json) if self.loading_index_json else {}

    def get_efficiency(self):
        return json.loads(self.efficiency_json) if self.efficiency_json else {}

    def get_baseline(self):
        return json.loads(self.baseline_json) if self.baseline_json else {}

    def get_fatigue(self):
        return json.loads(self.fatigue_json) if self.fatigue_json else {}

    def get_gait_cycles(self):
        return json.loads(self.gait_cycles_json) if self.gait_cycles_json else []
