"""
Personal Baseline Engine.
Uses first ~30s (or 25% of video, whichever is shorter) as baseline.
Computes deviations for each subsequent window.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

import numpy as np

from app.biomechanics.metrics_engine import BiomechanicsReport, WindowMetrics

logger = logging.getLogger(__name__)

BASELINE_FRACTION = 0.25      # use first 25% as baseline
BASELINE_MAX_S = 30.0         # cap at 30 seconds


@dataclass
class BaselineMetric:
    name: str
    baseline_value: Optional[float]
    unit: str
    note: str = ""


@dataclass
class PersonalBaseline:
    cadence_spm: Optional[float] = None
    stride_norm: Optional[float] = None
    vertical_osc: Optional[float] = None
    symmetry: Optional[float] = None
    trunk_lean: Optional[float] = None
    arm_swing: Optional[float] = None
    stride_consistency: Optional[float] = None
    baseline_windows: int = 0
    total_windows: int = 0
    notes: List[str] = field(default_factory=list)

    def compute_deviation(self, metric: str, current: Optional[float]) -> Optional[float]:
        """Return percentage deviation from baseline. Positive = above baseline."""
        baseline = getattr(self, metric, None)
        if baseline is None or current is None or baseline == 0:
            return None
        return round(((current - baseline) / abs(baseline)) * 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cadence_spm": self.cadence_spm,
            "stride_norm": self.stride_norm,
            "vertical_osc": self.vertical_osc,
            "symmetry": self.symmetry,
            "trunk_lean": self.trunk_lean,
            "arm_swing": self.arm_swing,
            "stride_consistency": self.stride_consistency,
            "baseline_windows": self.baseline_windows,
            "total_windows": self.total_windows,
            "notes": self.notes,
        }


def compute_personal_baseline(
    report: BiomechanicsReport,
    duration_s: float,
) -> PersonalBaseline:
    """
    Calculate personal baseline from the first portion of the run.
    Uses window data from BiomechanicsReport.
    """
    baseline = PersonalBaseline()
    windows = report.windows

    if not windows:
        baseline.notes.append("No window data available for baseline calculation.")
        return baseline

    baseline.total_windows = len(windows)
    baseline_fraction = min(BASELINE_FRACTION, BASELINE_MAX_S / max(duration_s, 1))
    n_baseline = max(1, int(len(windows) * baseline_fraction))
    baseline.baseline_windows = n_baseline

    b_windows = windows[:n_baseline]

    # Cadence
    cadences = [w.cadence_spm for w in b_windows if w.cadence_spm is not None]
    if cadences:
        baseline.cadence_spm = round(float(np.mean(cadences)), 1)

    # Stride consistency
    consistencies = [w.stride_consistency for w in b_windows if w.stride_consistency is not None]
    if consistencies:
        baseline.stride_consistency = round(float(np.mean(consistencies)), 1)

    # Vertical oscillation
    vertosc = [w.vertical_oscillation_norm for w in b_windows if w.vertical_oscillation_norm is not None]
    if vertosc:
        baseline.vertical_osc = round(float(np.mean(vertosc)), 4)

    # Symmetry
    syms = [w.symmetry_index for w in b_windows if w.symmetry_index is not None]
    if syms:
        baseline.symmetry = round(float(np.mean(syms)), 1)

    # Trunk lean
    trunks = [w.trunk_lean_mean for w in b_windows if w.trunk_lean_mean is not None]
    if trunks:
        baseline.trunk_lean = round(float(np.mean(trunks)), 1)

    # Arm swing
    arms = [w.arm_swing_mean for w in b_windows if w.arm_swing_mean is not None]
    if arms:
        baseline.arm_swing = round(float(np.mean(arms)), 1)

    if n_baseline == len(windows):
        baseline.notes.append(
            "Video is short — baseline covers the entire run. "
            "Personal deviation analysis requires a longer recording."
        )
    else:
        baseline.notes.append(
            f"Personal baseline computed from first {n_baseline} of {len(windows)} time windows "
            f"(approx. first {int(baseline_fraction * 100)}% of run)."
        )

    logger.info(f"Baseline: cadence={baseline.cadence_spm}, symmetry={baseline.symmetry}, "
                f"vertical_osc={baseline.vertical_osc}")
    return baseline


def compute_deviations(
    windows: List[WindowMetrics],
    baseline: PersonalBaseline,
) -> List[Dict[str, Any]]:
    """
    For each window beyond the baseline, compute deviation from baseline values.
    Returns a list of dicts with window index and per-metric deviations.
    """
    results = []
    n_baseline = baseline.baseline_windows

    for i, w in enumerate(windows):
        is_baseline = i < n_baseline
        dev = {
            "window_index": i,
            "time_pct_start": w.time_pct_start,
            "time_pct_end": w.time_pct_end,
            "time_s_start": w.time_s_start,
            "time_s_end": w.time_s_end,
            "is_baseline": is_baseline,
            "cadence_spm": w.cadence_spm,
            "symmetry": w.symmetry_index,
            "vertical_osc": w.vertical_oscillation_norm,
            "trunk_lean": w.trunk_lean_mean,
            "stride_consistency": w.stride_consistency,
            "arm_swing": w.arm_swing_mean,
        }

        if not is_baseline:
            dev["cadence_deviation_pct"] = baseline.compute_deviation("cadence_spm", w.cadence_spm)
            dev["symmetry_deviation_pct"] = baseline.compute_deviation("symmetry", w.symmetry_index)
            dev["vertical_osc_deviation_pct"] = baseline.compute_deviation("vertical_osc", w.vertical_oscillation_norm)
            dev["trunk_lean_deviation_pct"] = baseline.compute_deviation("trunk_lean", w.trunk_lean_mean)
            dev["stride_consistency_deviation_pct"] = baseline.compute_deviation("stride_consistency", w.stride_consistency)

        results.append(dev)

    return results
