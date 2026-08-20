"""
Running Style DNA Classifier.
Deterministic scoring across 8 biomechanical dimensions -> primary and secondary style archetypes.
All classifications provide transparent evidence directly from measured metrics.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

import numpy as np

from app.biomechanics.metrics_engine import BiomechanicsReport

logger = logging.getLogger(__name__)

# Style archetypes with explicit target profiles
STYLE_ARCHETYPES = [
    ("Glider",                   {"vertical": 90, "cadence": 80, "ground_contact": 65}),
    ("Bouncer",                  {"vertical": 25, "stride": 85, "cadence": 45}),
    ("High-Cadence Rhythm",      {"cadence": 90, "rhythm": 85, "stride": 50}),
    ("Power Stride",             {"stride": 85, "arm_swing": 80, "cadence": 50}),
    ("Compact Runner",           {"stride": 40, "vertical": 85, "arm_swing": 60}),
    ("Forward-Lean Drive",       {"posture": 90, "stride": 75, "cadence": 70}),
    ("Asymmetric Pattern",       {"symmetry": 35}),
    ("Balanced Runner",          {"cadence": 75, "posture": 80, "symmetry": 85, "rhythm": 80}),
]


@dataclass
class StyleDNA:
    cadence_score: float = 0.0
    stride_score: float = 0.0
    posture_score: float = 0.0
    symmetry_score: float = 0.0
    arm_swing_score: float = 0.0
    pelvic_stability_score: float = 0.0
    rhythm_score: float = 0.0
    vertical_score: float = 0.0

    primary_style: str = "Balanced Runner"
    secondary_style: Optional[str] = None
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cadence": round(self.cadence_score, 1),
            "stride": round(self.stride_score, 1),
            "posture": round(self.posture_score, 1),
            "symmetry": round(self.symmetry_score, 1),
            "arm_swing": round(self.arm_swing_score, 1),
            "pelvic_stability": round(self.pelvic_stability_score, 1),
            "rhythm": round(self.rhythm_score, 1),
            "vertical": round(self.vertical_score, 1),
            "primary_style": self.primary_style,
            "secondary_style": self.secondary_style,
            "evidence": self.evidence,
            "confidence": round(self.confidence, 2),
        }


def classify_style(report: BiomechanicsReport) -> StyleDNA:
    """
    Score each style dimension (0–100) deterministically from measured metrics,
    then identify the primary style archetype.
    """
    dna = StyleDNA()
    evidence: List[str] = []

    # 1. Cadence dimension
    if report.cadence and report.cadence.value is not None:
        cad = report.cadence.value
        # 140 SPM = 10, 180 SPM = 90, 190+ SPM = 100
        dna.cadence_score = float(np.clip((cad - 135.0) / (185.0 - 135.0) * 90.0 + 10.0, 5.0, 99.0))
        if cad >= 174:
            evidence.append(f"High step turnover rate ({cad:.0f} SPM).")
        elif cad <= 158:
            evidence.append(f"Lower cadence profile ({cad:.0f} SPM) with reliance on longer stride cycle.")
        else:
            evidence.append(f"Moderate cadence turnover ({cad:.0f} SPM).")
    else:
        dna.cadence_score = 60.0

    # 2. Stride ratio dimension
    if report.stride_normalized and report.stride_normalized.value is not None:
        stride = report.stride_normalized.value
        # 0.5x leg length = 20, 1.2x = 80
        dna.stride_score = float(np.clip((stride - 0.4) / (1.3 - 0.4) * 80.0 + 20.0, 10.0, 99.0))
        if stride > 1.05:
            evidence.append("Extended stride length relative to leg length.")
        elif stride < 0.70:
            evidence.append("Compact stride displacement.")
        else:
            evidence.append(f"Moderate stride displacement ratio ({stride:.2f}x).")
    else:
        dna.stride_score = 55.0

    # 3. Posture / Trunk Lean dimension
    if report.trunk_lean and report.trunk_lean.value is not None:
        lean = report.trunk_lean.value
        # 7.5° is optimal midpoint (100). Far deviations decrease score.
        dist = abs(lean - 7.5)
        dna.posture_score = float(np.clip(100.0 - dist * 5.5, 15.0, 99.0))
        if 5.0 <= lean <= 11.0:
            evidence.append(f"Optimal forward trunk lean ({lean:.1f}°).")
        elif lean > 14.0:
            evidence.append(f"Pronounced forward lean ({lean:.1f}°).")
        else:
            evidence.append(f"Upright vertical posture ({lean:.1f}°).")
    else:
        dna.posture_score = 65.0

    # 4. Movement Symmetry dimension
    if report.symmetry_index and report.symmetry_index.value is not None:
        dna.symmetry_score = float(np.clip(report.symmetry_index.value, 10.0, 99.0))
        sym = report.symmetry_index.value
        if sym >= 85:
            evidence.append(f"High bilateral kinematic symmetry ({sym:.0f}/100).")
        elif sym < 70:
            evidence.append(f"Noticeable left-right asymmetry ({sym:.0f}/100).")
    else:
        dna.symmetry_score = 75.0

    # 5. Arm Carriage dimension
    if report.arm_swing and report.arm_swing.value is not None:
        elbow = report.arm_swing.value
        opt_dist = abs(elbow - 90.0)
        dna.arm_swing_score = float(np.clip(100.0 - opt_dist * 2.2, 15.0, 99.0))
        if 78.0 <= elbow <= 102.0:
            evidence.append(f"Efficient 90° elbow carriage ({elbow:.0f}°).")
        elif elbow > 115.0:
            evidence.append(f"Extended arm swing pattern ({elbow:.0f}°).")
    else:
        dna.arm_swing_score = 65.0

    # 6. Pelvic Stability dimension
    if report.pelvic_stability and report.pelvic_stability.value is not None:
        dna.pelvic_stability_score = float(np.clip(report.pelvic_stability.value, 15.0, 99.0))
    else:
        dna.pelvic_stability_score = 70.0

    # 7. Rhythm Consistency dimension
    if report.rhythm_score and report.rhythm_score.value is not None:
        dna.rhythm_score = float(np.clip(report.rhythm_score.value, 15.0, 99.0))
        if report.rhythm_score.value >= 80:
            evidence.append("Consistent stride rhythm cadence.")
    else:
        dna.rhythm_score = 70.0

    # 8. Vertical Efficiency (low bounce = high score)
    if report.vertical_oscillation and report.vertical_oscillation.value is not None:
        vo = report.vertical_oscillation.value
        # 0.05 = 95, 0.20 = 20
        dna.vertical_score = float(np.clip(100.0 - (vo / 0.22) * 80.0, 10.0, 99.0))
        if vo < 0.08:
            evidence.append("Low vertical bounce (energy-conserving trajectory).")
        elif vo > 0.15:
            evidence.append("Higher vertical displacement during flight.")
    else:
        dna.vertical_score = 65.0

    scores = {
        "cadence": dna.cadence_score,
        "stride": dna.stride_score,
        "posture": dna.posture_score,
        "symmetry": dna.symmetry_score,
        "arm_swing": dna.arm_swing_score,
        "pelvic": dna.pelvic_stability_score,
        "rhythm": dna.rhythm_score,
        "vertical": dna.vertical_score,
        "ground_contact": 100.0 - (report.ground_contact_estimate.value or 30.0),
    }

    # Match primary and secondary archetypes
    ranked = sorted(
        [(name, _match_score(scores, target_profile)) for name, target_profile in STYLE_ARCHETYPES],
        key=lambda x: -x[1],
    )

    dna.primary_style = ranked[0][0]
    dna.confidence = round(float(ranked[0][1]), 2)
    dna.evidence = evidence

    if len(ranked) > 1 and ranked[1][1] >= 0.50:
        dna.secondary_style = ranked[1][0]

    logger.info(f"Style classification: {dna.primary_style} (conf={dna.confidence:.2f})")
    return dna


def _match_score(scores: Dict[str, float], targets: Dict[str, float]) -> float:
    """Calculates match coefficient (0.0 to 1.0) against archetype target profile."""
    diffs = []
    for dim, target_val in targets.items():
        actual = scores.get(dim, 60.0)
        # Distance error
        diff = abs(actual - target_val)
        diffs.append(max(0.0, 1.0 - diff / 55.0))
    return float(np.mean(diffs)) if diffs else 0.5
