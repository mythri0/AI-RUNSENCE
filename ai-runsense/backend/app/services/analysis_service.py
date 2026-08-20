"""
Analysis Service — orchestrates the full pipeline:
Upload → Validate → Pose → Temporal → Gait → Metrics →
Baseline → Fatigue → Loading → Style → Mistakes → Priorities → Coach → Persist
"""
from __future__ import annotations
import json
import logging
import os
import numpy as np
from typing import Optional, Callable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, np.bool_): return bool(obj)
        return super().default(obj)

from app.models.db_models import RunSession, Runner
from app.cv.video_validator import validate_video
from app.cv.video_processor import process_video, rewrite_analysis_video
from app.biomechanics.temporal_tracker import TemporalTracker
from app.biomechanics.gait_cycle import detect_gait_cycles
from app.biomechanics.metrics_engine import compute_metrics
from app.biomechanics.personal_baseline import compute_personal_baseline, compute_deviations
from app.biomechanics.fatigue_detector import detect_fatigue
from app.biomechanics.loading_index import compute_loading_index
from app.classification.style_classifier import classify_style
from app.classification.mistake_detector import detect_mistakes
from app.coaching.priority_engine import compute_priorities
from app.coaching.ai_coach import generate_coaching

logger = logging.getLogger(__name__)

PROCESSED_DIR = "data/processed"


async def run_analysis(
    session_id: int,
    db: AsyncSession,
    progress_callback: Optional[Callable[[float, str], None]] = None,
):
    """Full analysis pipeline for a given session."""

    def _progress(pct: float, msg: str):
        logger.info(f"[Session {session_id}] {pct:.0f}% — {msg}")
        if progress_callback:
            progress_callback(pct, msg)

    # ── Load session ───────────────────────────────────────────────────────────
    result = await db.execute(select(RunSession).where(RunSession.id == session_id))
    session: RunSession = result.scalar_one_or_none()
    if not session:
        raise RuntimeError(f"Session {session_id} not found")

    runner_result = await db.execute(select(Runner).where(Runner.id == session.runner_id))
    runner: Runner = runner_result.scalar_one_or_none()

    video_path = os.path.join("data/uploads", session.video_filename)
    if not os.path.exists(video_path):
        await _set_error(session, db, "Video file not found on server.")
        return

    try:
        # ── Stage 1: Video Validation ──────────────────────────────────────────
        await _update_status(session, db, "processing", 5.0, "Validating video…")
        _progress(5.0, "Validating video…")

        val = validate_video(video_path)
        if not val.valid:
            await _set_error(session, db, " | ".join(val.errors))
            return

        session.video_duration_s = val.duration_s
        session.video_fps = val.fps
        session.video_width = val.width
        session.video_height = val.height
        await db.commit()

        # ── Stage 2: Pose Estimation ───────────────────────────────────────────
        await _update_status(session, db, "processing", 10.0, "Running pose estimation…")
        _progress(10.0, "Running pose estimation…")

        def pose_progress(pct: float, msg: str):
            overall = 10 + pct * 0.55   # maps pose 0–90% → overall 10–60%
            _progress(overall, msg)

        all_landmarks = process_video(
            input_path=video_path,
            output_dir=PROCESSED_DIR,
            session_id=session_id,
            progress_callback=pose_progress,
        )

        if not all_landmarks:
            await _set_error(session, db, "No pose data could be extracted from the video.")
            return

        # ── Stage 3: Temporal Tracking ─────────────────────────────────────────
        await _update_status(session, db, "processing", 62.0, "Building temporal trajectories…")
        _progress(62.0, "Building temporal trajectories…")
        tracker = TemporalTracker(all_landmarks)

        # ── Stage 4: Gait-Cycle Detection ──────────────────────────────────────
        await _update_status(session, db, "processing", 66.0, "Detecting gait cycles…")
        _progress(66.0, "Detecting gait cycles…")
        gait = detect_gait_cycles(tracker, val.fps)

        # ── Stage 5: Biomechanics Metrics ─────────────────────────────────────
        await _update_status(session, db, "processing", 70.0, "Computing biomechanical metrics…")
        _progress(70.0, "Computing biomechanical metrics…")
        report = compute_metrics(tracker, gait, val.fps)

        # ── Stage 6: Personal Baseline ────────────────────────────────────────
        await _update_status(session, db, "processing", 74.0, "Computing personal baseline…")
        _progress(74.0, "Computing personal baseline…")
        baseline = compute_personal_baseline(report, val.duration_s)
        window_deviations = compute_deviations(report.windows, baseline)

        # ── Stage 7: Fatigue Detection ────────────────────────────────────────
        await _update_status(session, db, "processing", 78.0, "Analyzing form degradation…")
        _progress(78.0, "Analyzing form degradation…")
        fatigue = detect_fatigue(window_deviations, val.duration_s)

        # ── Stage 8: Loading Index ────────────────────────────────────────────
        await _update_status(session, db, "processing", 81.0, "Computing loading index…")
        _progress(81.0, "Computing loading index…")
        weight_kg = runner.weight_kg if runner else None
        loading = compute_loading_index(report, weight_kg)

        # ── Stage 9: Style Classification ────────────────────────────────────
        await _update_status(session, db, "processing", 83.0, "Classifying running style…")
        _progress(83.0, "Classifying running style…")
        style = classify_style(report)

        # ── Stage 10: Mistake Detection ───────────────────────────────────────
        await _update_status(session, db, "processing", 85.0, "Detecting form issues…")
        _progress(85.0, "Detecting form issues…")
        mistakes = detect_mistakes(
            report, gait, baseline,
            val.duration_s,
            distance_type=session.distance_type,
        )

        # ── Stage 11: Priority Ranking ────────────────────────────────────────
        await _update_status(session, db, "processing", 87.0, "Ranking priorities…")
        _progress(87.0, "Ranking priorities…")
        priorities = compute_priorities(mistakes, session_goal=session.session_goal)

        # ── Stage 12: AI Coach ────────────────────────────────────────────────
        await _update_status(session, db, "processing", 89.0, "Generating AI coaching…")
        _progress(89.0, "Generating AI coaching…")

        metrics_dict = _report_to_dict(report)
        analysis_input = {
            "metrics": metrics_dict,
            "baseline": baseline.to_dict(),
            "mistakes": [m.to_dict() for m in mistakes],
            "priorities": [p.to_dict() for p in priorities],
            "fatigue": fatigue.to_dict(),
            "style": style.to_dict(),
            "context": {
                "distance_type": session.distance_type,
                "environment": session.environment,
                "session_goal": session.session_goal,
            },
            "runner": {
                "age": runner.age if runner else None,
                "weight_kg": runner.weight_kg if runner else None,
                "experience_level": runner.experience_level if runner else None,
            },
        }
        coach = generate_coaching(analysis_input)

        # ── Stage 13: Timeline ────────────────────────────────────────────────
        timeline = _build_timeline(window_deviations, fatigue, val.duration_s)

        # ── Stage 14: Efficiency Score ────────────────────────────────────────
        efficiency = _compute_efficiency_score(report, style)

        # ── Stage 15: Rewrite analysis video with mistake annotations ─────────
        await _update_status(session, db, "processing", 92.0, "Writing annotated video…")
        _progress(92.0, "Writing annotated video…")
        mistake_ts_map = {
            m.timestamp_s: {"label": m.name, "highlight_joints": m.highlight_joints}
            for m in mistakes
            if m.timestamp_s is not None
        }
        if mistake_ts_map:
            try:
                rewrite_analysis_video(video_path, PROCESSED_DIR, session_id, all_landmarks, mistake_ts_map)
            except Exception as e:
                logger.warning(f"Analysis video rewrite failed: {e}")

        # ── Persist ───────────────────────────────────────────────────────────
        await _update_status(session, db, "processing", 97.0, "Saving results…")
        _progress(97.0, "Saving results…")

        session.metrics_json = json.dumps(metrics_dict, cls=NumpyEncoder)
        session.baseline_json = json.dumps(baseline.to_dict(), cls=NumpyEncoder)
        session.mistakes_json = json.dumps([m.to_dict() for m in mistakes], cls=NumpyEncoder)
        session.fatigue_json = json.dumps(fatigue.to_dict(), cls=NumpyEncoder)
        session.style_json = json.dumps(style.to_dict(), cls=NumpyEncoder)
        session.priorities_json = json.dumps([p.to_dict() for p in priorities], cls=NumpyEncoder)
        session.coach_json = json.dumps(coach, cls=NumpyEncoder)
        session.timeline_json = json.dumps(timeline, cls=NumpyEncoder)
        session.loading_index_json = json.dumps(loading.to_dict(), cls=NumpyEncoder)
        session.efficiency_json = json.dumps(efficiency, cls=NumpyEncoder)
        session.gait_cycles_json = json.dumps([{
            "index": c.index,
            "start_frame": c.start_frame,
            "end_frame": c.end_frame,
            "start_time_s": c.start_time_s,
            "end_time_s": c.end_time_s,
            "duration_s": c.duration_s,
            "confidence": c.confidence,
        } for c in gait.cycles], cls=NumpyEncoder)

        # Aggregate for evolution
        session.efficiency_score = efficiency.get("overall", 0)
        session.cadence_mean = report.cadence.value if report.cadence else None
        session.symmetry_mean = report.symmetry_index.value if report.symmetry_index else None
        session.posture_score = style.posture_score
        session.fatigue_detected = fatigue.detected
        session.primary_style = style.primary_style
        session.status = "done"
        session.processing_stage = "Complete"
        session.processing_progress = 100.0

        await db.commit()
        _progress(100.0, "Analysis complete!")
        logger.info(f"Session {session_id} analysis complete.")

    except Exception as e:
        logger.exception(f"Analysis pipeline error for session {session_id}: {e}")
        await _set_error(session, db, f"Analysis failed: {str(e)[:300]}")


async def _update_status(session: RunSession, db: AsyncSession, status: str, progress: float, stage: str):
    session.status = status
    session.processing_progress = progress
    session.processing_stage = stage
    await db.commit()


async def _set_error(session: RunSession, db: AsyncSession, message: str):
    session.status = "error"
    session.error_message = message
    session.processing_stage = "Error"
    await db.commit()
    logger.error(f"Session {session.id} error: {message}")


def _report_to_dict(report) -> dict:
    def _metric_dict(m):
        if m is None:
            return None
        return {
            "value": m.value,
            "unit": m.unit,
            "label": m.label,
            "estimated": m.estimated,
            "confidence": m.confidence,
            "note": m.note,
        }

    return {
        "cadence": _metric_dict(report.cadence),
        "stride_normalized": _metric_dict(report.stride_normalized),
        "vertical_oscillation": _metric_dict(report.vertical_oscillation),
        "symmetry_index": _metric_dict(report.symmetry_index),
        "trunk_lean": _metric_dict(report.trunk_lean),
        "knee_angle_left": _metric_dict(report.knee_angle_left),
        "knee_angle_right": _metric_dict(report.knee_angle_right),
        "arm_swing": _metric_dict(report.arm_swing),
        "ground_contact_estimate": _metric_dict(report.ground_contact_estimate),
        "foot_strike": report.foot_strike,
        "pelvic_stability": _metric_dict(report.pelvic_stability),
        "rhythm_score": _metric_dict(report.rhythm_score),
        "windows": [
            {
                "window_index": w.window_index,
                "time_pct_start": w.time_pct_start,
                "time_pct_end": w.time_pct_end,
                "time_s_start": w.time_s_start,
                "time_s_end": w.time_s_end,
                "cadence_spm": w.cadence_spm,
                "symmetry_index": w.symmetry_index,
                "vertical_oscillation_norm": w.vertical_oscillation_norm,
                "stride_consistency": w.stride_consistency,
                "trunk_lean_mean": w.trunk_lean_mean,
                "arm_swing_mean": w.arm_swing_mean,
                "ground_contact_proxy": w.ground_contact_proxy,
            }
            for w in report.windows
        ],
    }


def _build_timeline(window_deviations: list, fatigue, duration_s: float) -> list:
    """Build form-quality timeline points from window deviations."""
    points = []
    onset_idx = fatigue.onset_window_index if fatigue.detected else None

    for w in window_deviations:
        idx = w["window_index"]
        is_baseline = w.get("is_baseline", False)

        # Determine form quality from deviations
        neg_devs = []
        for key in ["cadence_deviation_pct", "symmetry_deviation_pct", "stride_consistency_deviation_pct"]:
            val = w.get(key)
            if val is not None and val < 0:
                neg_devs.append(abs(val))

        pos_devs = []
        for key in ["vertical_osc_deviation_pct", "trunk_lean_deviation_pct"]:
            val = w.get(key)
            if val is not None and val > 0:
                pos_devs.append(val)

        total_concern = sum(neg_devs) + sum(pos_devs)
        is_degrading = fatigue.detected and onset_idx is not None and idx >= onset_idx

        if is_baseline or total_concern < 5:
            quality = "good"
            color = "green"
        elif total_concern < 12:
            quality = "fair"
            color = "yellow"
        elif is_degrading or total_concern < 25:
            quality = "poor"
            color = "orange"
        else:
            quality = "degrading"
            color = "red"

        notes = []
        if is_degrading:
            notes.append("Potential form degradation")
        if w.get("cadence_deviation_pct") and w["cadence_deviation_pct"] < -5:
            notes.append(f"Cadence {w['cadence_deviation_pct']:.1f}% from baseline")
        if w.get("symmetry_deviation_pct") and w["symmetry_deviation_pct"] < -5:
            notes.append(f"Symmetry {w['symmetry_deviation_pct']:.1f}% from baseline")

        points.append({
            "window_index": idx,
            "time_pct": (w["time_pct_start"] + w["time_pct_end"]) / 2,
            "timestamp_s": w["time_s_start"],
            "form_quality": quality,
            "color": color,
            "notes": notes,
            "is_baseline": is_baseline,
        })

    return points


def _compute_efficiency_score(report, style) -> dict:
    """Compute overall efficiency score 0–100 from style dimensions."""
    components = {
        "cadence": style.cadence_score,
        "stride": style.stride_score,
        "posture": style.posture_score,
        "symmetry": style.symmetry_score,
        "arm_swing": style.arm_swing_score,
        "pelvic_stability": style.pelvic_stability_score,
        "rhythm": style.rhythm_score,
        "vertical": style.vertical_score,
    }
    # Weighted average
    weights = {
        "cadence": 0.20, "stride": 0.12, "posture": 0.15, "symmetry": 0.18,
        "arm_swing": 0.10, "pelvic_stability": 0.10, "rhythm": 0.10, "vertical": 0.05,
    }
    overall = sum(components[k] * weights[k] for k in weights)
    return {"overall": round(overall, 1), "components": {k: round(v, 1) for k, v in components.items()}}
