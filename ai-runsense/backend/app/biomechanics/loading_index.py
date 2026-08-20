"""
Physics-Informed Estimated Mechanical Loading Index.
Transparent 0–100 analytical proxy. NOT a direct measurement of GRF or joint torques.
Each contributor is documented and justified.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

import numpy as np

from app.biomechanics.metrics_engine import BiomechanicsReport

logger = logging.getLogger(__name__)

# Reference population values for normalization
REF_CADENCE = 170.0          # steps/min (efficient midfoot runner reference)
REF_VERT_OSC = 0.04          # image height fraction (typical efficient runner)
REF_SYMMETRY = 90.0          # symmetry score


@dataclass
class LoadingContributor:
    name: str
    contribution: float     # 0–25 scale per component
    explanation: str


@dataclass
class LoadingIndexResult:
    index: float            # 0–100
    level: str              # Low / Moderate / Elevated / High
    contributors: List[LoadingContributor] = field(default_factory=list)
    mass_included: bool = False
    disclaimer: str = (
        "This is an estimated analytical proxy for relative mechanical demand, "
        "not a direct measurement of ground-reaction force or joint loading."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": round(self.index, 1),
            "level": self.level,
            "contributors": [{"name": c.name, "contribution": round(c.contribution, 1), "explanation": c.explanation}
                             for c in self.contributors],
            "mass_included": self.mass_included,
            "disclaimer": self.disclaimer,
        }


def compute_loading_index(
    report: BiomechanicsReport,
    weight_kg: Optional[float] = None,
) -> LoadingIndexResult:
    """
    Compute an estimated mechanical loading index from available biomechanical signals.
    Score 0–100 where higher = estimated higher mechanical demand.
    """
    contributors: List[LoadingContributor] = []
    total = 0.0

    # ── 1. Vertical Oscillation Proxy (0–25) ─────────────────────────────────
    vert_score = 12.5  # default mid
    if report.vertical_oscillation and report.vertical_oscillation.value is not None:
        vo = report.vertical_oscillation.value
        # Higher oscillation = higher loading proxy
        ratio = vo / REF_VERT_OSC
        vert_score = float(np.clip(ratio * 12.5, 0, 25))
    contributors.append(LoadingContributor(
        name="Vertical Oscillation",
        contribution=vert_score,
        explanation="Higher vertical movement increases estimated impact demand at landing.",
    ))
    total += vert_score

    # ── 2. Cadence Deviation (0–20) ───────────────────────────────────────────
    cad_score = 10.0
    if report.cadence and report.cadence.value is not None:
        cad = report.cadence.value
        # Low cadence = longer stride = higher estimated loading
        deviation = max(0.0, (REF_CADENCE - cad) / REF_CADENCE)
        cad_score = float(np.clip(deviation * 40, 0, 20))
    contributors.append(LoadingContributor(
        name="Cadence Deviation",
        contribution=cad_score,
        explanation="Lower cadence may be associated with longer ground contact and higher impact per step.",
    ))
    total += cad_score

    # ── 3. Symmetry Index (0–20) ──────────────────────────────────────────────
    sym_score = 10.0
    if report.symmetry_index and report.symmetry_index.value is not None:
        sym = report.symmetry_index.value
        asym = max(0.0, REF_SYMMETRY - sym)
        sym_score = float(np.clip((asym / REF_SYMMETRY) * 25, 0, 20))
    contributors.append(LoadingContributor(
        name="Asymmetry Pattern",
        contribution=sym_score,
        explanation="Greater asymmetry may concentrate mechanical demand on one side.",
    ))
    total += sym_score

    # ── 4. Stride Consistency / Rhythm (0–15) ────────────────────────────────
    rhythm_score = 7.5
    if report.rhythm_score and report.rhythm_score.value is not None:
        rhythm = report.rhythm_score.value
        inconsistency = max(0.0, 100.0 - rhythm)
        rhythm_score = float(np.clip((inconsistency / 100) * 15, 0, 15))
    contributors.append(LoadingContributor(
        name="Rhythm Inconsistency",
        contribution=rhythm_score,
        explanation="Variable stride rhythm may create irregular impact patterns.",
    ))
    total += rhythm_score

    # ── 5. Trunk Lean (0–10) ─────────────────────────────────────────────────
    trunk_score = 5.0
    if report.trunk_lean and report.trunk_lean.value is not None:
        lean = report.trunk_lean.value
        # Excessive lean (>15°) or very low lean (<3°) both have implications
        lean_dev = abs(lean - 7.0)   # 7° is approximate efficient range midpoint
        trunk_score = float(np.clip((lean_dev / 15) * 10, 0, 10))
    contributors.append(LoadingContributor(
        name="Trunk Lean Pattern",
        contribution=trunk_score,
        explanation="Excessive or insufficient trunk lean may alter load distribution.",
    ))
    total += trunk_score

    # ── 6. Body Mass Factor (0–10, only if mass provided) ────────────────────
    mass_included = False
    if weight_kg is not None and weight_kg > 0:
        # Heavier runners have higher absolute GRF; normalize to 70 kg reference
        mass_factor = float(np.clip((weight_kg / 70.0 - 1.0) * 5, -5, 10))
        mass_score = max(0.0, 5.0 + mass_factor)
        contributors.append(LoadingContributor(
            name="Body Mass Factor",
            contribution=mass_score,
            explanation=f"User-provided body mass ({weight_kg:.0f} kg) scales absolute loading estimate.",
        ))
        total += mass_score
        mass_included = True

    # Normalize to 0–100 scale
    max_possible = 25 + 20 + 20 + 15 + 10 + (10 if mass_included else 0)
    index = float(np.clip((total / max_possible) * 100, 0, 100))

    if index < 35:
        level = "Low"
    elif index < 55:
        level = "Moderate"
    elif index < 75:
        level = "Elevated"
    else:
        level = "High"

    logger.info(f"Loading Index: {index:.1f}/100 ({level})")
    return LoadingIndexResult(
        index=index,
        level=level,
        contributors=contributors,
        mass_included=mass_included,
    )
