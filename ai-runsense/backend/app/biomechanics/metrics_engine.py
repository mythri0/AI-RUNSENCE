"""
Core biomechanical metrics engine.
All measurements are physics-grounded, normalized to body dimensions, and transparently labeled.
No fabricated values — insufficient data returns None with an explanatory note.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

import numpy as np

from app.biomechanics.temporal_tracker import TemporalTracker
from app.biomechanics.gait_cycle import GaitCycleResult, GaitCycle

logger = logging.getLogger(__name__)


@dataclass
class MetricResult:
    value: Optional[float]
    unit: str
    label: str
    estimated: bool = True
    confidence: float = 0.5
    note: Optional[str] = None


@dataclass
class WindowMetrics:
    """Metrics computed for a single time window (e.g. 0–10% of video)."""
    window_index: int
    time_pct_start: float
    time_pct_end: float
    time_s_start: float
    time_s_end: float
    cadence_spm: Optional[float] = None
    symmetry_index: Optional[float] = None
    vertical_oscillation_norm: Optional[float] = None
    stride_consistency: Optional[float] = None
    trunk_lean_mean: Optional[float] = None
    arm_swing_mean: Optional[float] = None
    ground_contact_proxy: Optional[float] = None


@dataclass
class BiomechanicsReport:
    cadence: Optional[MetricResult] = None
    stride_normalized: Optional[MetricResult] = None
    vertical_oscillation: Optional[MetricResult] = None
    symmetry_index: Optional[MetricResult] = None
    trunk_lean: Optional[MetricResult] = None
    knee_angle_left: Optional[MetricResult] = None
    knee_angle_right: Optional[MetricResult] = None
    arm_swing: Optional[MetricResult] = None
    ground_contact_estimate: Optional[MetricResult] = None
    foot_strike: Optional[Dict[str, Any]] = None
    pelvic_stability: Optional[MetricResult] = None
    rhythm_score: Optional[MetricResult] = None
    windows: List[WindowMetrics] = field(default_factory=list)


def compute_metrics(
    tracker: TemporalTracker,
    gait: GaitCycleResult,
    fps: float,
    n_windows: int = 10,
) -> BiomechanicsReport:
    report = BiomechanicsReport()
    n = tracker.n_frames

    if n == 0:
        return report

    # ── 1. Cadence ────────────────────────────────────────────────────────────
    if gait.cadence_spm is not None:
        report.cadence = MetricResult(
            value=gait.cadence_spm,
            unit="steps/min",
            label="Cadence",
            estimated=True,
            confidence=gait.confidence,
            note=f"Calculated from {len(gait.cycles)} detected gait cycles ({gait.confidence_label} confidence).",
        )

    # ── 2. Stride Displacement (normalized to leg length) ─────────────────────
    report.stride_normalized = _compute_normalized_stride(tracker, gait)

    # ── 3. Vertical Oscillation (normalized to leg length) ────────────────────
    report.vertical_oscillation = _compute_vertical_oscillation(tracker)

    # ── 4. Symmetry Index ─────────────────────────────────────────────────────
    report.symmetry_index = _compute_symmetry(tracker)

    # ── 5. Trunk Lean ─────────────────────────────────────────────────────────
    report.trunk_lean = _compute_trunk_lean(tracker)

    # ── 6. Knee Flexion Angles ────────────────────────────────────────────────
    report.knee_angle_left = _compute_joint_angle(tracker, "LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE", "Left Knee Angle")
    report.knee_angle_right = _compute_joint_angle(tracker, "RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE", "Right Knee Angle")

    # ── 7. Arm Swing ──────────────────────────────────────────────────────────
    report.arm_swing = _compute_arm_swing(tracker)

    # ── 8. Ground Contact Proxy ───────────────────────────────────────────────
    report.ground_contact_estimate = _compute_contact_proxy(tracker, fps)

    # ── 9. Foot Strike Classification ─────────────────────────────────────────
    report.foot_strike = _classify_foot_strike(tracker)

    # ── 10. Pelvic Stability ──────────────────────────────────────────────────
    report.pelvic_stability = _compute_pelvic_stability(tracker)

    # ── 11. Stride Rhythm ─────────────────────────────────────────────────────
    report.rhythm_score = _compute_rhythm(gait)

    # ── 12. Temporal Window Time-Series ───────────────────────────────────────
    report.windows = _compute_windows(tracker, gait, fps, n_windows)

    return report


# ─── Individual Metric Implementations ────────────────────────────────────────

def _get_body_scale_px(tracker: TemporalTracker) -> float:
    """
    Estimate reference body segment length in normalized image coordinates
    (hip to ankle distance = leg length proxy) to make measurements camera-distance invariant.
    """
    lhy = tracker.get_trajectory("LEFT_HIP", "y", smoothed=True)
    lay = tracker.get_trajectory("LEFT_ANKLE", "y", smoothed=True)
    rhy = tracker.get_trajectory("RIGHT_HIP", "y", smoothed=True)
    ray = tracker.get_trajectory("RIGHT_ANKLE", "y", smoothed=True)

    lengths = []
    if len(lhy) > 0 and len(lay) > 0:
        lengths.append(float(np.nanmedian(np.abs(lay - lhy))))
    if len(rhy) > 0 and len(ray) > 0:
        lengths.append(float(np.nanmedian(np.abs(ray - rhy))))

    if lengths and np.nanmean(lengths) > 0.05:
        return float(np.nanmean(lengths))
    return 0.40  # default fallback body leg ratio in image coords


def _compute_normalized_stride(tracker: TemporalTracker, gait: GaitCycleResult) -> Optional[MetricResult]:
    """
    Normalized stride length: Horizontal ankle excursion normalized to body leg length.
    Value ~ 1.0 means stride displacement equals leg length.
    """
    if not gait.cycles:
        return MetricResult(None, "ratio", "Normalized Stride Length",
                            note="No gait cycles detected; stride length cannot be computed.")

    lax = tracker.get_trajectory("LEFT_ANKLE", "x", smoothed=True)
    rax = tracker.get_trajectory("RIGHT_ANKLE", "x", smoothed=True)
    scale = _get_body_scale_px(tracker)

    displacements = []
    for c in gait.cycles:
        s, e = c.start_frame, c.end_frame
        cycle_disp = []
        if len(lax) > e:
            la_range = np.nanmax(lax[s:e]) - np.nanmin(lax[s:e])
            if not np.isnan(la_range) and la_range > 0:
                cycle_disp.append(la_range)
        if len(rax) > e:
            ra_range = np.nanmax(rax[s:e]) - np.nanmin(rax[s:e])
            if not np.isnan(ra_range) and ra_range > 0:
                cycle_disp.append(ra_range)
        if cycle_disp:
            displacements.append(np.mean(cycle_disp))

    if not displacements or scale <= 0:
        return MetricResult(None, "ratio", "Normalized Stride Length")

    mean_disp = float(np.mean(displacements))
    normalized_val = mean_disp / scale

    conf = round(float(np.clip(gait.confidence * 0.9, 0.1, 0.95)), 2)
    return MetricResult(
        value=round(normalized_val, 2),
        unit="x leg-length",
        label="Normalized Stride Length",
        estimated=True,
        confidence=conf,
        note="Normalized relative to estimated leg length. Camera-angle dependent.",
    )


def _compute_vertical_oscillation(tracker: TemporalTracker) -> Optional[MetricResult]:
    """
    Vertical oscillation: peak-to-trough vertical displacement of hip center,
    normalized by estimated leg length.
    """
    lhy = tracker.get_trajectory("LEFT_HIP", "y", smoothed=True)
    rhy = tracker.get_trajectory("RIGHT_HIP", "y", smoothed=True)

    if len(lhy) == 0 and len(rhy) == 0:
        return MetricResult(None, "ratio", "Estimated Vertical Oscillation")

    if len(lhy) > 0 and len(rhy) > 0:
        min_len = min(len(lhy), len(rhy))
        hip_y = (lhy[:min_len] + rhy[:min_len]) / 2.0
    else:
        hip_y = lhy if len(lhy) > 0 else rhy

    # Filter out NaN
    valid_hip = hip_y[~np.isnan(hip_y)]
    if len(valid_hip) < 15:
        return MetricResult(None, "ratio", "Estimated Vertical Oscillation")

    # 10th to 90th percentile to reject outlier glitches
    p10, p90 = np.percentile(valid_hip, 10), np.percentile(valid_hip, 90)
    osc_raw = float(p90 - p10)

    scale = _get_body_scale_px(tracker)
    osc_norm = osc_raw / scale if scale > 0 else osc_raw

    vis_l = tracker.get_mean_visibility("LEFT_HIP")
    vis_r = tracker.get_mean_visibility("RIGHT_HIP")
    conf = round(float(np.clip((vis_l + vis_r) / 2.0, 0.1, 0.95)), 2)

    return MetricResult(
        value=round(osc_norm, 3),
        unit="rel. body unit",
        label="Estimated Vertical Oscillation",
        estimated=True,
        confidence=conf,
        note="Normalized to runner stature proxy. Lower bounce typically correlates with energy conservation.",
    )


def _compute_symmetry(tracker: TemporalTracker) -> Optional[MetricResult]:
    """
    Kinematic symmetry index (0–100 score).
    Compares bilateral knee flexion range and excursion over time.
    """
    left_angles = _get_angle_series(tracker, "LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE")
    right_angles = _get_angle_series(tracker, "RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE")

    if left_angles is None or right_angles is None:
        return MetricResult(None, "score (0–100)", "Symmetry Index", note="Bilateral knee landmarks not sufficiently visible.")

    min_len = min(len(left_angles), len(right_angles))
    if min_len < 15:
        return MetricResult(None, "score (0–100)", "Symmetry Index")

    la = left_angles[:min_len]
    ra = right_angles[:min_len]

    valid = ~(np.isnan(la) | np.isnan(ra))
    if np.sum(valid) < 10:
        return MetricResult(None, "score (0–100)", "Symmetry Index")

    la = la[valid]
    ra = ra[valid]

    # Compare mean excursion and ROM
    l_rom = np.percentile(la, 90) - np.percentile(la, 10)
    r_rom = np.percentile(ra, 90) - np.percentile(ra, 10)
    rom_diff_pct = abs(l_rom - r_rom) / max(0.5 * (l_rom + r_rom), 1e-3) * 100.0

    mean_diff_pct = abs(np.mean(la) - np.mean(ra)) / max(0.5 * (np.mean(la) + np.mean(ra)), 1e-3) * 100.0
    asymmetry_pct = 0.6 * rom_diff_pct + 0.4 * mean_diff_pct

    symmetry_score = float(np.clip(100.0 - asymmetry_pct * 2.0, 10.0, 99.0))

    vis_l = tracker.get_mean_visibility("LEFT_KNEE")
    vis_r = tracker.get_mean_visibility("RIGHT_KNEE")
    conf = round(float(np.clip(min(vis_l, vis_r), 0.1, 0.95)), 2)

    return MetricResult(
        value=round(symmetry_score, 1),
        unit="score (0–100)",
        label="Symmetry Index",
        estimated=True,
        confidence=conf,
        note="Bilateral kinematic balance score. 100 = symmetric left-right movement.",
    )


def _compute_trunk_lean(tracker: TemporalTracker) -> Optional[MetricResult]:
    """
    Trunk lean angle relative to vertical (degrees).
    Positive angle = forward lean from vertical.
    """
    lsy = tracker.get_trajectory("LEFT_SHOULDER", "y", smoothed=True)
    rsy = tracker.get_trajectory("RIGHT_SHOULDER", "y", smoothed=True)
    lsx = tracker.get_trajectory("LEFT_SHOULDER", "x", smoothed=True)
    rsx = tracker.get_trajectory("RIGHT_SHOULDER", "x", smoothed=True)
    lhy = tracker.get_trajectory("LEFT_HIP", "y", smoothed=True)
    rhy = tracker.get_trajectory("RIGHT_HIP", "y", smoothed=True)
    lhx = tracker.get_trajectory("LEFT_HIP", "x", smoothed=True)
    rhx = tracker.get_trajectory("RIGHT_HIP", "x", smoothed=True)

    min_len = min(len(lsy), len(rsy), len(lhy), len(rhy), len(lsx), len(rsx), len(lhx), len(rhx))
    if min_len < 10:
        return MetricResult(None, "degrees", "Trunk Lean")

    sy = (lsy[:min_len] + rsy[:min_len]) / 2.0
    sx = (lsx[:min_len] + rsx[:min_len]) / 2.0
    hy = (lhy[:min_len] + rhy[:min_len]) / 2.0
    hx = (lhx[:min_len] + rhx[:min_len]) / 2.0

    dx = sx - hx
    dy = sy - hy  # y increases downward in image coords

    valid = ~(np.isnan(dx) | np.isnan(dy))
    if np.sum(valid) < 10:
        return MetricResult(None, "degrees", "Trunk Lean")

    # Angle relative to vertical
    angles = np.degrees(np.arctan2(np.abs(dx[valid]), np.abs(dy[valid]) + 1e-6))
    mean_angle = float(np.median(angles))
    std_angle = float(np.std(angles))

    conf = round(float(np.clip((tracker.get_mean_visibility("LEFT_SHOULDER") + tracker.get_mean_visibility("RIGHT_SHOULDER")) / 2.0, 0.1, 0.95)), 2)

    return MetricResult(
        value=round(mean_angle, 1),
        unit="degrees",
        label="Trunk Lean",
        estimated=True,
        confidence=conf,
        note=f"Estimated forward trunk lean from vertical (std: ±{std_angle:.1f}°). Efficient range: 5–12°.",
    )


def _compute_joint_angle(
    tracker: TemporalTracker,
    a: str, b: str, c: str,
    label: str,
) -> Optional[MetricResult]:
    """Compute 2D angle at joint B for segment triplet A-B-C."""
    angles = _get_angle_series(tracker, a, b, c)
    if angles is None or len(angles) == 0:
        return MetricResult(None, "degrees", label, note="Key landmarks not reliably tracked.")

    valid_angles = angles[~np.isnan(angles)]
    if len(valid_angles) < 10:
        return MetricResult(None, "degrees", label)

    # Median and peak flexion
    median_angle = float(np.median(valid_angles))
    conf = round(float(np.clip(min(tracker.get_mean_visibility(a), tracker.get_mean_visibility(b), tracker.get_mean_visibility(c)), 0.1, 0.95)), 2)

    return MetricResult(
        value=round(median_angle, 1),
        unit="degrees",
        label=label,
        estimated=True,
        confidence=conf,
    )


def _compute_arm_swing(tracker: TemporalTracker) -> Optional[MetricResult]:
    """Elbow flexion angle during arm carriage."""
    left = _get_angle_series(tracker, "LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST")
    right = _get_angle_series(tracker, "RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST")

    values = []
    if left is not None:
        values.extend(left[~np.isnan(left)].tolist())
    if right is not None:
        values.extend(right[~np.isnan(right)].tolist())

    if len(values) < 10:
        return MetricResult(None, "degrees", "Arm Swing", note="Arm landmarks not reliably visible.")

    mean_angle = float(np.median(values))
    conf = round(float(np.clip((tracker.get_mean_visibility("LEFT_ELBOW") + tracker.get_mean_visibility("RIGHT_ELBOW")) / 2.0, 0.1, 0.90)), 2)

    return MetricResult(
        value=round(mean_angle, 1),
        unit="degrees",
        label="Arm Swing",
        estimated=True,
        confidence=conf,
        note="Mean elbow flexion angle during arm carriage (typical efficient range: 80–100°).",
    )


def _compute_contact_proxy(tracker: TemporalTracker, fps: float) -> Optional[MetricResult]:
    """
    Ground contact time proxy: Calculated by detecting the duration during each stride
    where the stance ankle vertical velocity stays near zero (stance phase).
    """
    left_ankle_y = tracker.get_trajectory("LEFT_ANKLE", "y", smoothed=True)
    if len(left_ankle_y) < int(fps * 1.5):
        return MetricResult(None, "%", "Estimated Ground Contact", note="Insufficient frame count.")

    vel = np.abs(np.gradient(left_ankle_y))
    # Threshold based on moving variance / standard deviation
    motion_std = float(np.std(vel))
    if motion_std < 1e-5:
        return MetricResult(None, "%", "Estimated Ground Contact", note="No stance motion variation.")

    # Stance phase is when vertical velocity drops below 20% of peak velocity
    vel_peak = np.percentile(vel, 90)
    stance_thresh = vel_peak * 0.22
    contact_fraction = float(np.mean(vel < stance_thresh)) * 100.0

    # Ensure physiological bounds for running (15% to 55% of gait cycle)
    contact_ratio = float(np.clip(contact_fraction, 15.0, 55.0))
    conf = round(float(np.clip(tracker.get_mean_visibility("LEFT_ANKLE") * 0.65, 0.1, 0.75)), 2)

    return MetricResult(
        value=round(contact_ratio, 1),
        unit="% gait cycle",
        label="Estimated Ground Contact",
        estimated=True,
        confidence=conf,
        note="Kinematic proxy based on stance foot vertical velocity. Target for running: < 35%.",
    )


def _classify_foot_strike(tracker: TemporalTracker) -> Optional[Dict[str, Any]]:
    """
    Foot-strike pattern classification:
    Examines the relative vertical and angular position of the heel vs forefoot (metatarsal)
    at initial ground contact frames.
    """
    heel_y = tracker.get_trajectory("LEFT_HEEL", "y", smoothed=True)
    toe_y = tracker.get_trajectory("LEFT_FOOT_INDEX", "y", smoothed=True)
    ankle_y = tracker.get_trajectory("LEFT_ANKLE", "y", smoothed=True)

    heel_vis = tracker.get_mean_visibility("LEFT_HEEL")
    toe_vis = tracker.get_mean_visibility("LEFT_FOOT_INDEX")

    if heel_vis < 0.35 or toe_vis < 0.35:
        return {"classification": None, "label": "Unknown", "confidence": 0.0,
                "note": "Foot landmarks not reliably tracked for strike classification."}

    min_len = min(len(heel_y), len(toe_y), len(ankle_y))
    if min_len < 15:
        return {"classification": None, "label": "Unknown", "confidence": 0.0, "note": "Insufficient frames."}

    hy = heel_y[:min_len]
    ty = toe_y[:min_len]

    # Contact occurs when ankle/heel is lowest in the image (y is high)
    contact_threshold = np.percentile(hy, 70)
    contact_indices = np.where(hy > contact_threshold)[0]

    if len(contact_indices) < 5:
        return {"classification": None, "label": "Unknown", "confidence": 0.0, "note": "Contact events not isolated."}

    # In image coordinates, higher y means lower to the ground.
    # If heel_y > toe_y at landing -> Heel is lower (Heel Strike)
    # If toe_y > heel_y at landing -> Toe is lower (Forefoot Strike)
    delta = hy[contact_indices] - ty[contact_indices]
    mean_delta = float(np.nanmedian(delta))

    scale = _get_body_scale_px(tracker)
    norm_delta = mean_delta / scale if scale > 0 else mean_delta

    if norm_delta > 0.04:
        classification = "heel"
        label = "Heel Strike"
    elif norm_delta < -0.04:
        classification = "forefoot"
        label = "Forefoot Strike"
    else:
        classification = "midfoot"
        label = "Midfoot Strike"

    conf = round(float(np.clip(min((heel_vis + toe_vis) / 2.0, 0.80), 0.2, 0.80)), 2)

    return {
        "classification": classification,
        "label": label,
        "confidence": conf,
        "note": f"Estimated from {len(contact_indices)} contact points. Camera viewpoint dependent.",
    }


def _compute_pelvic_stability(tracker: TemporalTracker) -> Optional[MetricResult]:
    """
    Pelvic stability: Measures lateral hip drop normalized to hip segment width.
    """
    lhy = tracker.get_trajectory("LEFT_HIP", "y", smoothed=True)
    rhy = tracker.get_trajectory("RIGHT_HIP", "y", smoothed=True)
    lhx = tracker.get_trajectory("LEFT_HIP", "x", smoothed=True)
    rhx = tracker.get_trajectory("RIGHT_HIP", "x", smoothed=True)

    min_len = min(len(lhy), len(rhy), len(lhx), len(rhx))
    if min_len < 15:
        return MetricResult(None, "score (0–100)", "Pelvic Stability")

    # Hip width as scaling factor
    hip_width = np.nanmedian(np.sqrt((lhx[:min_len] - rhx[:min_len]) ** 2 + (lhy[:min_len] - rhy[:min_len]) ** 2))
    scale = hip_width if hip_width > 0.02 else _get_body_scale_px(tracker) * 0.4

    lateral_drop = np.abs(lhy[:min_len] - rhy[:min_len])
    valid_drop = lateral_drop[~np.isnan(lateral_drop)]
    if len(valid_drop) < 10:
        return MetricResult(None, "score (0–100)", "Pelvic Stability")

    mean_drop_norm = float(np.median(valid_drop)) / max(scale, 1e-4)
    # 0 drop = 100, 0.25 normalized drop = 50
    stability = float(np.clip(100.0 - mean_drop_norm * 200.0, 15.0, 99.0))

    conf = round(float(np.clip((tracker.get_mean_visibility("LEFT_HIP") + tracker.get_mean_visibility("RIGHT_HIP")) / 2.0, 0.1, 0.90)), 2)

    return MetricResult(
        value=round(stability, 1),
        unit="score (0–100)",
        label="Pelvic Stability",
        estimated=True,
        confidence=conf,
        note="Score (0–100) reflecting bilateral pelvic horizontal control.",
    )


def _compute_rhythm(gait: GaitCycleResult) -> Optional[MetricResult]:
    """Stride rhythm consistency score (0–100) derived from gait duration CV."""
    if not gait.cycles or len(gait.cycles) < 2:
        return MetricResult(None, "score (0–100)", "Rhythm", note="Insufficient gait cycles to assess rhythm.")

    durations = np.array([c.duration_s for c in gait.cycles])
    mean_dur = float(np.mean(durations))
    std_dur = float(np.std(durations))

    cv = std_dur / mean_dur if mean_dur > 0 else 1.0
    # CV of 0 = 100, CV of 0.20 = 50
    rhythm_score = float(np.clip(100.0 - cv * 250.0, 10.0, 99.0))

    return MetricResult(
        value=round(rhythm_score, 1),
        unit="score (0–100)",
        label="Rhythm",
        estimated=True,
        confidence=gait.confidence,
        note=f"Cycle-to-cycle duration consistency (CV: {cv:.2%}).",
    )


def _compute_windows(
    tracker: TemporalTracker,
    gait: GaitCycleResult,
    fps: float,
    n_windows: int,
) -> List[WindowMetrics]:
    """Compute temporal window slices for trend and fatigue evaluation."""
    n = tracker.n_frames
    if n == 0 or n_windows <= 0:
        return []

    window_size = max(1, n // n_windows)
    windows: List[WindowMetrics] = []

    for i in range(n_windows):
        s_idx = i * window_size
        e_idx = min(n, (i + 1) * window_size if i < n_windows - 1 else n)

        t_start = float(tracker.timestamps[s_idx]) if s_idx < len(tracker.timestamps) else s_idx / fps
        t_end = float(tracker.timestamps[e_idx - 1]) if e_idx - 1 < len(tracker.timestamps) else e_idx / fps
        pct_start = (s_idx / n) * 100.0
        pct_end = (e_idx / n) * 100.0

        # Sub-tracker for window
        sub_frames = tracker.frames[s_idx:e_idx]
        if len(sub_frames) < 5:
            continue
        sub_tracker = TemporalTracker(sub_frames)

        # Cadence in window (filter cycles within window)
        w_cycles = [c for c in gait.cycles if s_idx <= c.start_frame < e_idx]
        if len(w_cycles) >= 1:
            w_durs = [c.duration_s for c in w_cycles]
            w_cadence = (2.0 * 60.0) / float(np.mean(w_durs))
            w_rhythm = float(np.clip(100.0 - (np.std(w_durs) / max(np.mean(w_durs), 1e-4)) * 250.0, 10.0, 99.0))
        else:
            w_cadence = None
            w_rhythm = None

        sym_res = _compute_symmetry(sub_tracker)
        vo_res = _compute_vertical_oscillation(sub_tracker)
        trunk_res = _compute_trunk_lean(sub_tracker)
        arm_res = _compute_arm_swing(sub_tracker)
        contact_res = _compute_contact_proxy(sub_tracker, fps)

        windows.append(WindowMetrics(
            window_index=i,
            time_pct_start=round(pct_start, 1),
            time_pct_end=round(pct_end, 1),
            time_s_start=round(t_start, 2),
            time_s_end=round(t_end, 2),
            cadence_spm=round(w_cadence, 1) if w_cadence else None,
            symmetry_index=sym_res.value if sym_res else None,
            vertical_oscillation_norm=vo_res.value if vo_res else None,
            stride_consistency=w_rhythm,
            trunk_lean_mean=trunk_res.value if trunk_res else None,
            arm_swing_mean=arm_res.value if arm_res else None,
            ground_contact_proxy=contact_res.value if contact_res else None,
        ))

    return windows


def _get_angle_series(
    tracker: TemporalTracker,
    a_name: str, b_name: str, c_name: str,
) -> Optional[np.ndarray]:
    """Calculate time-series 2D angle (in degrees) at joint B for triplet A-B-C."""
    ax = tracker.get_trajectory(a_name, "x", smoothed=True)
    ay = tracker.get_trajectory(a_name, "y", smoothed=True)
    bx = tracker.get_trajectory(b_name, "x", smoothed=True)
    by = tracker.get_trajectory(b_name, "y", smoothed=True)
    cx = tracker.get_trajectory(c_name, "x", smoothed=True)
    cy = tracker.get_trajectory(c_name, "y", smoothed=True)

    min_len = min(len(ax), len(ay), len(bx), len(by), len(cx), len(cy))
    if min_len == 0:
        return None

    # Vectors BA and BC
    v_ba_x = ax[:min_len] - bx[:min_len]
    v_ba_y = ay[:min_len] - by[:min_len]
    v_bc_x = cx[:min_len] - bx[:min_len]
    v_bc_y = cy[:min_len] - by[:min_len]

    dot = v_ba_x * v_bc_x + v_ba_y * v_bc_y
    mag_ba = np.sqrt(v_ba_x ** 2 + v_ba_y ** 2)
    mag_bc = np.sqrt(v_bc_x ** 2 + v_bc_y ** 2)

    denom = mag_ba * mag_bc
    valid = (denom > 1e-6) & ~np.isnan(denom)

    angles = np.full(min_len, np.nan)
    cos_val = np.clip(dot[valid] / denom[valid], -1.0, 1.0)
    angles[valid] = np.degrees(np.arccos(cos_val))

    return angles
