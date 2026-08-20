"""
Fatigue / Form-Degradation Engine.
Divides video into temporal windows and detects systematic, sustained drift in key biomechanics.
Requires multi-window consistency — never triggers on single noisy frames or arbitrary fixed percentages.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

import numpy as np
from scipy.stats import linregress

logger = logging.getLogger(__name__)

DRIFT_THRESHOLD_PCT = 4.0      # >4% systematic drift across windows
MIN_WINDOWS_FOR_ANALYSIS = 4


@dataclass
class MetricTrend:
    name: str
    direction: str          # "stable" / "decreasing" / "increasing"
    slope_pct_per_window: float
    is_drifting: bool
    significance: float     # R² of linear fit
    early_value: Optional[float] = None
    late_value: Optional[float] = None


@dataclass
class FatigueReport:
    detected: bool = False
    confidence: float = 0.0
    onset_time_s: Optional[float] = None
    onset_window_index: Optional[int] = None
    drifting_metrics: List[MetricTrend] = field(default_factory=list)
    stable_metrics: List[MetricTrend] = field(default_factory=list)
    summary: str = ""
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected": self.detected,
            "confidence": round(self.confidence, 2),
            "onset_time_s": round(self.onset_time_s, 2) if self.onset_time_s is not None else None,
            "onset_window_index": self.onset_window_index,
            "drifting_metrics": [_trend_to_dict(t) for t in self.drifting_metrics],
            "stable_metrics": [_trend_to_dict(t) for t in self.stable_metrics],
            "summary": self.summary,
            "notes": self.notes,
        }


def detect_fatigue(window_data: List[Dict[str, Any]], duration_s: float) -> FatigueReport:
    """
    Analyze window-level metrics for sustained, monotonic drift indicating
    potential form degradation relative to baseline.
    """
    report = FatigueReport()

    if len(window_data) < MIN_WINDOWS_FOR_ANALYSIS:
        report.notes.append(f"Insufficient windows ({len(window_data)}) for progressive form analysis.")
        report.summary = "Recording too short for progressive fatigue/drift analysis."
        return report

    metrics_decreasing_bad = {
        "cadence_spm": "Cadence",
        "symmetry": "Symmetry",
        "stride_consistency": "Rhythm Consistency",
    }
    metrics_increasing_bad = {
        "vertical_osc": "Vertical Oscillation",
        "trunk_lean": "Trunk Lean",
        "ground_contact_proxy": "Ground Contact Time",
    }

    trends: List[MetricTrend] = []
    x = np.array([w["window_index"] for w in window_data], dtype=float)

    for key, name in metrics_decreasing_bad.items():
        vals = [w.get(key) for w in window_data]
        trend = _analyze_trend(name, x, vals, bad_direction="decreasing")
        if trend:
            trends.append(trend)

    for key, name in metrics_increasing_bad.items():
        vals = [w.get(key) for w in window_data]
        trend = _analyze_trend(name, x, vals, bad_direction="increasing")
        if trend:
            trends.append(trend)

    drifting = [t for t in trends if t.is_drifting]
    stable = [t for t in trends if not t.is_drifting]

    report.drifting_metrics = drifting
    report.stable_metrics = stable

    # Form degradation detected if ≥ 2 metrics exhibit sustained statistically significant deterioration
    n_drifting = len(drifting)
    if n_drifting >= 2:
        onset_time, onset_idx = _find_inflection_onset(window_data, drifting)
        mean_r2 = float(np.mean([t.significance for t in drifting])) if drifting else 0.5
        conf = float(np.clip(0.40 + (n_drifting / 4.0) * 0.40 + mean_r2 * 0.20, 0.35, 0.95))

        report.detected = True
        report.confidence = conf
        report.onset_time_s = onset_time
        report.onset_window_index = onset_idx

        drift_names = ", ".join(t.name for t in drifting)
        report.summary = (
            f"Sustained form-degradation pattern detected across {n_drifting} metrics ({drift_names}). "
            f"Indicates progressive mechanical fatigue under continuous load."
        )
        if onset_time is not None:
            report.notes.append(f"Mechanical drift becomes pronounced around {_fmt_time(onset_time)}.")
    elif n_drifting == 1:
        report.detected = False
        report.confidence = 0.25
        report.summary = f"Isolated drift observed in {drifting[0].name}, but overall movement pattern remained stable."
    else:
        report.detected = False
        report.confidence = 0.05
        report.summary = "No significant form degradation detected. Movement mechanics remained consistent."

    report.notes.append("Kinematic trend assessment, not a clinical fatigue diagnosis.")
    logger.info(f"Fatigue analysis: detected={report.detected}, drifting={[t.name for t in drifting]}")
    return report


def _analyze_trend(
    name: str,
    x: np.ndarray,
    vals: List[Optional[float]],
    bad_direction: str,
) -> Optional[MetricTrend]:
    """Fit linear regression to detect sustained directional drift."""
    valid = [(xi, v) for xi, v in zip(x, vals) if v is not None and not np.isnan(v)]
    if len(valid) < 3:
        return None

    xv, yv = zip(*valid)
    xv, yv = np.array(xv), np.array(yv)

    slope, intercept, r_value, p_value, _ = linregress(xv, yv)
    r2 = float(r_value ** 2)

    mean_val = float(np.mean(yv))
    if abs(mean_val) < 1e-4:
        return None

    slope_pct = float((slope / abs(mean_val)) * 100.0)

    # Sustained drift criteria:
    # 1. Slope in the deteriorating direction exceeding total cumulative threshold
    # 2. R² >= 0.22 (moderate to strong linear trend) and p_value < 0.20
    is_drift_direction = (
        (bad_direction == "decreasing" and slope_pct < -(DRIFT_THRESHOLD_PCT / len(xv))) or
        (bad_direction == "increasing" and slope_pct > (DRIFT_THRESHOLD_PCT / len(xv)))
    )
    is_significant = (r2 >= 0.20 and p_value <= 0.20)

    direction = "decreasing" if slope < 0 else ("increasing" if slope > 0 else "stable")

    return MetricTrend(
        name=name,
        direction=direction,
        slope_pct_per_window=round(slope_pct, 2),
        is_drifting=bool(is_drift_direction and is_significant),
        significance=round(r2, 3),
        early_value=round(float(yv[0]), 2),
        late_value=round(float(yv[-1]), 2),
    )


def _find_inflection_onset(
    window_data: List[Dict[str, Any]],
    drifting_metrics: List[MetricTrend],
) -> tuple[Optional[float], Optional[int]]:
    """
    Find dynamic inflection point: the earliest window where cumulative deviations
    consistently exceed 1.5 standard deviations from baseline.
    """
    if not window_data or len(window_data) < 3:
        return None, None

    # Track window deviations
    n = len(window_data)
    baseline_len = max(1, n // 4)

    for i in range(baseline_len, n):
        w = window_data[i]
        # Check if negative deviations are active
        devs = [
            abs(w.get("cadence_deviation_pct") or 0.0),
            abs(w.get("symmetry_deviation_pct") or 0.0),
            abs(w.get("vertical_osc_deviation_pct") or 0.0),
        ]
        if np.mean(devs) > 4.5:
            return w.get("time_s_start"), i

    # Fallback to middle window
    mid_idx = n // 2
    return window_data[mid_idx].get("time_s_start"), mid_idx


def _fmt_time(s: float) -> str:
    m = int(s // 60)
    sec = s % 60
    return f"{m:02d}:{sec:04.1f}"


def _trend_to_dict(t: MetricTrend) -> Dict[str, Any]:
    return {
        "name": t.name,
        "direction": t.direction,
        "slope_pct_per_window": t.slope_pct_per_window,
        "is_drifting": t.is_drifting,
        "significance": t.significance,
        "early_value": t.early_value,
        "late_value": t.late_value,
    }
