"""
Mistake Detector.
Detects biomechanical form issues and assigns exact frame numbers and timestamps for video replay.
Context-aware thresholds with personal baseline integration.
"""
from __future__ import annotations
import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

import numpy as np

from app.biomechanics.metrics_engine import BiomechanicsReport
from app.biomechanics.gait_cycle import GaitCycleResult
from app.biomechanics.personal_baseline import PersonalBaseline

logger = logging.getLogger(__name__)

SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"


@dataclass
class Mistake:
    id: str
    name: str
    severity: str
    confidence: float
    evidence: str
    timestamp_s: Optional[float]
    frame_number: Optional[int]
    relevant_metrics: Dict[str, Any]
    possible_effect: str
    suggested_correction: str
    highlight_joints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "severity": self.severity,
            "confidence": round(self.confidence, 2),
            "evidence": self.evidence,
            "timestamp_s": round(self.timestamp_s, 2) if self.timestamp_s is not None else None,
            "frame_number": self.frame_number,
            "relevant_metrics": self.relevant_metrics,
            "possible_effect": self.possible_effect,
            "suggested_correction": self.suggested_correction,
            "highlight_joints": self.highlight_joints,
        }


def detect_mistakes(
    report: BiomechanicsReport,
    gait: GaitCycleResult,
    baseline: PersonalBaseline,
    duration_s: float,
    distance_type: Optional[str] = None,
) -> List[Mistake]:
    """Run all biomechanical defect detectors and assign exact video timestamps."""
    mistakes: List[Mistake] = []

    _check_low_cadence(report, gait, baseline, distance_type, mistakes)
    _check_high_vertical_oscillation(report, gait, baseline, mistakes)
    _check_poor_symmetry(report, gait, baseline, mistakes)
    _check_trunk_lean(report, gait, mistakes)
    _check_arm_swing(report, gait, mistakes)
    _check_pelvic_instability(report, gait, baseline, mistakes)
    _check_rhythm(report, gait, baseline, mistakes)
    _check_overstride(report, gait, mistakes)

    # Sort by severity then confidence
    sev_order = {SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 1, SEVERITY_LOW: 2}
    mistakes.sort(key=lambda m: (sev_order.get(m.severity, 3), -m.confidence))

    logger.info(f"Mistakes detected: {[m.name for m in mistakes]}")
    return mistakes


def _get_cycle_moment(gait: GaitCycleResult, index: int = 0) -> tuple[Optional[float], Optional[int]]:
    """Helper to get timestamp and frame number from a gait cycle."""
    if gait.cycles:
        idx = min(len(gait.cycles) - 1, max(0, index))
        c = gait.cycles[idx]
        return c.start_time_s, c.start_frame
    return None, None


# ─── Individual Detectors ─────────────────────────────────────────────────────

def _check_low_cadence(
    report: BiomechanicsReport,
    gait: GaitCycleResult,
    baseline: PersonalBaseline,
    distance_type: Optional[str],
    mistakes: List[Mistake],
):
    if not report.cadence or report.cadence.value is None:
        return

    cad = report.cadence.value
    # Dynamic thresholds based on event type
    if distance_type == "sprint":
        thresh = 180.0
    elif distance_type in ("marathon", "ultra"):
        thresh = 158.0
    else:
        thresh = 166.0

    baseline_dev = baseline.compute_deviation("cadence_spm", cad)
    is_low_abs = cad < thresh
    is_low_rel = baseline_dev is not None and baseline_dev < -6.0

    if not is_low_abs and not is_low_rel:
        return

    severity = SEVERITY_HIGH if cad < (thresh - 14.0) else SEVERITY_MEDIUM
    evidence_parts = [f"Measured cadence ({cad:.0f} SPM) is below the efficient target range ({thresh:.0f}+ SPM)."]
    if is_low_rel and baseline.cadence_spm:
        evidence_parts.append(f"Fell {abs(baseline_dev):.1f}% below your early baseline of {baseline.cadence_spm:.0f} SPM.")

    # Find longest duration cycle (slowest cadence event)
    worst_idx = 0
    if gait.cycles:
        durations = [c.duration_s for c in gait.cycles]
        worst_idx = int(np.argmax(durations))

    ts, fn = _get_cycle_moment(gait, worst_idx)

    mistakes.append(Mistake(
        id=str(uuid.uuid4())[:8],
        name="Low Cadence",
        severity=severity,
        confidence=min(report.cadence.confidence, 0.90),
        evidence=" ".join(evidence_parts),
        timestamp_s=ts,
        frame_number=fn,
        relevant_metrics={"cadence_spm": cad, "target_threshold": thresh, "baseline": baseline.cadence_spm},
        possible_effect="Lower step frequency increases ground contact time and braking forces on each foot strike.",
        suggested_correction="Gradually increase cadence by 5–8% through quicker leg turnover rather than forceful push-off.",
        highlight_joints=["LEFT_ANKLE", "RIGHT_ANKLE"],
    ))


def _check_high_vertical_oscillation(
    report: BiomechanicsReport,
    gait: GaitCycleResult,
    baseline: PersonalBaseline,
    mistakes: List[Mistake],
):
    if not report.vertical_oscillation or report.vertical_oscillation.value is None:
        return

    vo = report.vertical_oscillation.value
    baseline_dev = baseline.compute_deviation("vertical_osc", vo)

    # Threshold on normalized oscillation
    is_high = vo > 0.12
    is_high_rel = baseline_dev is not None and baseline_dev > 15.0

    if not is_high and not is_high_rel:
        return

    severity = SEVERITY_HIGH if vo > 0.16 else SEVERITY_MEDIUM
    evidence = f"Estimated vertical displacement ratio ({vo:.2f}) indicates excess upward bounce."
    if is_high_rel and baseline.vertical_osc:
        evidence += f" Rose {abs(baseline_dev):.1f}% above your baseline window ({baseline.vertical_osc:.2f})."

    ts, fn = _get_cycle_moment(gait, len(gait.cycles) // 2 if gait.cycles else 0)

    mistakes.append(Mistake(
        id=str(uuid.uuid4())[:8],
        name="Excessive Vertical Movement",
        severity=severity,
        confidence=min(report.vertical_oscillation.confidence, 0.85),
        evidence=evidence,
        timestamp_s=ts,
        frame_number=fn,
        relevant_metrics={"vertical_oscillation_ratio": vo, "baseline": baseline.vertical_osc},
        possible_effect="Excess upward propulsion diverts metabolic energy away from forward propulsion.",
        suggested_correction="Focus on driving forward horizontally and landing lightly with knees soft.",
        highlight_joints=["LEFT_HIP", "RIGHT_HIP"],
    ))


def _check_poor_symmetry(
    report: BiomechanicsReport,
    gait: GaitCycleResult,
    baseline: PersonalBaseline,
    mistakes: List[Mistake],
):
    if not report.symmetry_index or report.symmetry_index.value is None:
        return

    sym = report.symmetry_index.value
    baseline_dev = baseline.compute_deviation("symmetry", sym)

    if sym >= 75.0 and (baseline_dev is None or baseline_dev >= -8.0):
        return

    severity = SEVERITY_HIGH if sym < 62.0 else SEVERITY_MEDIUM
    evidence = f"Bilateral symmetry index ({sym:.0f}/100) indicates asymmetric leg loading."
    if baseline_dev and baseline_dev < -8.0:
        evidence += f" Dropped {abs(baseline_dev):.1f}% compared to initial baseline."

    ts, fn = _get_cycle_moment(gait, 0)

    mistakes.append(Mistake(
        id=str(uuid.uuid4())[:8],
        name="Movement Asymmetry",
        severity=severity,
        confidence=min(report.symmetry_index.confidence, 0.85),
        evidence=evidence,
        timestamp_s=ts,
        frame_number=fn,
        relevant_metrics={"symmetry_index": sym, "baseline": baseline.symmetry},
        possible_effect="Unbalanced movement concentrates mechanical load unevenly across joints and soft tissue.",
        suggested_correction="Incorporate unilateral strength exercises (single-leg squats, step-ups) and mindful bilateral pacing.",
        highlight_joints=["LEFT_KNEE", "RIGHT_KNEE", "LEFT_ANKLE", "RIGHT_ANKLE"],
    ))


def _check_trunk_lean(
    report: BiomechanicsReport,
    gait: GaitCycleResult,
    mistakes: List[Mistake],
):
    if not report.trunk_lean or report.trunk_lean.value is None:
        return

    lean = report.trunk_lean.value
    ts, fn = _get_cycle_moment(gait, 0)

    if lean > 14.5:
        mistakes.append(Mistake(
            id=str(uuid.uuid4())[:8],
            name="Excessive Trunk Lean",
            severity=SEVERITY_HIGH if lean > 18.0 else SEVERITY_MEDIUM,
            confidence=min(report.trunk_lean.confidence, 0.80),
            evidence=f"Forward trunk lean angle ({lean:.1f}°) exceeds efficient reference range (5–12°).",
            timestamp_s=ts,
            frame_number=fn,
            relevant_metrics={"trunk_lean_degrees": lean},
            possible_effect="Excessive forward lean places increased demand on lower back extensors and alters hip extension.",
            suggested_correction="Think about running tall with chest open and slight forward lean originating from the ankles.",
            highlight_joints=["LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_HIP", "RIGHT_HIP"],
        ))
    elif lean < 3.0:
        mistakes.append(Mistake(
            id=str(uuid.uuid4())[:8],
            name="Very Upright Posture",
            severity=SEVERITY_LOW,
            confidence=min(report.trunk_lean.confidence, 0.75),
            evidence=f"Trunk posture is overly vertical ({lean:.1f}°). Slight forward lean (5–10°) aids forward momentum.",
            timestamp_s=ts,
            frame_number=fn,
            relevant_metrics={"trunk_lean_degrees": lean},
            possible_effect="Completely vertical posture can cause braking forces and hinder natural hip extension.",
            suggested_correction="Allow a subtle forward lean from the ankles while maintaining a relaxed, tall spine.",
            highlight_joints=["LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_HIP", "RIGHT_HIP"],
        ))


def _check_arm_swing(
    report: BiomechanicsReport,
    gait: GaitCycleResult,
    mistakes: List[Mistake],
):
    if not report.arm_swing or report.arm_swing.value is None:
        return

    angle = report.arm_swing.value
    ts, fn = _get_cycle_moment(gait, 0)

    if angle > 118.0:
        mistakes.append(Mistake(
            id=str(uuid.uuid4())[:8],
            name="Poor Arm Swing (Over-Extended)",
            severity=SEVERITY_LOW,
            confidence=min(report.arm_swing.confidence, 0.75),
            evidence=f"Mean elbow angle ({angle:.0f}°) is extended beyond the compact 80–100° range.",
            timestamp_s=ts,
            frame_number=fn,
            relevant_metrics={"arm_swing_angle": angle},
            possible_effect="Extended arms increase rotational inertia and slow arm cadence.",
            suggested_correction="Maintain roughly 90° elbow flexion and drive arms straight backward in rhythm with stride.",
            highlight_joints=["LEFT_ELBOW", "RIGHT_ELBOW", "LEFT_WRIST", "RIGHT_WRIST"],
        ))
    elif angle < 62.0:
        mistakes.append(Mistake(
            id=str(uuid.uuid4())[:8],
            name="Poor Arm Swing (Restricted)",
            severity=SEVERITY_LOW,
            confidence=min(report.arm_swing.confidence, 0.75),
            evidence=f"Elbows are held tightly flexed ({angle:.0f}°), limiting fluid arm drive.",
            timestamp_s=ts,
            frame_number=fn,
            relevant_metrics={"arm_swing_angle": angle},
            possible_effect="Restricted arm swing can create upper body tension and reduce stride counterbalancing.",
            suggested_correction="Relax shoulders and allow hands to travel naturally between hip and lower ribcage.",
            highlight_joints=["LEFT_ELBOW", "RIGHT_ELBOW"],
        ))


def _check_pelvic_instability(
    report: BiomechanicsReport,
    gait: GaitCycleResult,
    baseline: PersonalBaseline,
    mistakes: List[Mistake],
):
    if not report.pelvic_stability or report.pelvic_stability.value is None:
        return

    stab = report.pelvic_stability.value
    if stab >= 70.0:
        return

    ts, fn = _get_cycle_moment(gait, 0)
    mistakes.append(Mistake(
        id=str(uuid.uuid4())[:8],
        name="Pelvic Instability",
        severity=SEVERITY_HIGH if stab < 55.0 else SEVERITY_MEDIUM,
        confidence=min(report.pelvic_stability.confidence, 0.80),
        evidence=f"Pelvic stability score ({stab:.0f}/100) reflects lateral hip drop during single-leg stance.",
        timestamp_s=ts,
        frame_number=fn,
        relevant_metrics={"pelvic_stability_score": stab},
        possible_effect="Excessive pelvic drop increases lateral torque on the knee and hip abductors.",
        suggested_correction="Gluteus medius strengthening (side planks, lateral band walks) improves pelvic levelness.",
        highlight_joints=["LEFT_HIP", "RIGHT_HIP"],
    ))


def _check_rhythm(
    report: BiomechanicsReport,
    gait: GaitCycleResult,
    baseline: PersonalBaseline,
    mistakes: List[Mistake],
):
    if not report.rhythm_score or report.rhythm_score.value is None:
        return

    rhythm = report.rhythm_score.value
    if rhythm >= 68.0:
        return

    ts, fn = _get_cycle_moment(gait, 0)
    mistakes.append(Mistake(
        id=str(uuid.uuid4())[:8],
        name="Cadence Instability",
        severity=SEVERITY_MEDIUM if rhythm < 50.0 else SEVERITY_LOW,
        confidence=min(gait.confidence, 0.80),
        evidence=f"Stride rhythm score ({rhythm:.0f}/100) indicates irregular cycle duration variation.",
        timestamp_s=ts,
        frame_number=fn,
        relevant_metrics={"rhythm_score": rhythm},
        possible_effect="Inconsistent stride pacing increases energy expenditure and disrupts pacing economy.",
        suggested_correction="Focus on an even tempo rhythm using breathing cadence cues or a running metronome.",
        highlight_joints=["LEFT_ANKLE", "RIGHT_ANKLE"],
    ))


def _check_overstride(
    report: BiomechanicsReport,
    gait: GaitCycleResult,
    mistakes: List[Mistake],
):
    if not report.cadence or not report.stride_normalized:
        return
    if report.cadence.value is None or report.stride_normalized.value is None:
        return

    cad = report.cadence.value
    stride = report.stride_normalized.value

    # Overstride pattern: low cadence combined with excessive stride displacement
    if cad < 162.0 and stride > 1.10:
        ts, fn = _get_cycle_moment(gait, 0)
        mistakes.append(Mistake(
            id=str(uuid.uuid4())[:8],
            name="Over-Striding Pattern",
            severity=SEVERITY_HIGH if (cad < 155.0 and stride > 1.25) else SEVERITY_MEDIUM,
            confidence=min(gait.confidence * 0.9, 0.85),
            evidence=f"Foot landing pattern shows extended stride ({stride:.2f}x leg length) paired with low cadence ({cad:.0f} SPM).",
            timestamp_s=ts,
            frame_number=fn,
            relevant_metrics={"cadence_spm": cad, "stride_normalized": stride},
            possible_effect="Landing ahead of the center of mass increases braking forces and impact loading on the knee joint.",
            suggested_correction="Shorten stride and land with foot positioned closer to underneath hips.",
            highlight_joints=["LEFT_ANKLE", "RIGHT_ANKLE", "LEFT_KNEE", "RIGHT_KNEE"],
        ))
