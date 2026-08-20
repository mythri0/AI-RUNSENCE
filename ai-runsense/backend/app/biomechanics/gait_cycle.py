"""
Gait-cycle discovery via ankle trajectory analysis + foot-strike event detection.
Detects running cycle boundaries from kinematic landmarks without hardcoded frame counts.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
from scipy.signal import find_peaks, correlate
from scipy.fft import fft, fftfreq

from app.biomechanics.temporal_tracker import TemporalTracker

logger = logging.getLogger(__name__)

MIN_CYCLES = 2
MIN_CYCLE_CONFIDENCE = 0.35


@dataclass
class GaitCycle:
    index: int
    start_frame: int
    end_frame: int
    start_time_s: float
    end_time_s: float
    duration_s: float
    confidence: float   # 0–1


@dataclass
class GaitCycleResult:
    cycles: List[GaitCycle] = field(default_factory=list)
    cadence_spm: Optional[float] = None     # steps per minute
    cycle_duration_mean_s: Optional[float] = None
    cycle_duration_std_s: Optional[float] = None
    confidence: float = 0.0
    confidence_label: str = "Low"
    method: str = "peak_detection"
    notes: List[str] = field(default_factory=list)


def detect_gait_cycles(tracker: TemporalTracker, fps: float) -> GaitCycleResult:
    """
    Detect gait cycles using kinematic trajectory analysis:
    1. Primary: Ankle vertical position extrema (foot strike & swing events)
    2. Fallback: Knee flexion or Hip vertical oscillation if ankle is occluded
    3. Autocorrelation & spectral analysis to validate periodicity and compute confidence
    """
    result = GaitCycleResult()
    n = tracker.n_frames

    if n < max(20, int(fps * 1.5)):
        result.notes.append("Video duration too short for reliable gait-cycle detection.")
        return result

    left_ankle_y = tracker.get_trajectory("LEFT_ANKLE", "y", smoothed=True)
    right_ankle_y = tracker.get_trajectory("RIGHT_ANKLE", "y", smoothed=True)
    left_vis = tracker.get_mean_visibility("LEFT_ANKLE")
    right_vis = tracker.get_mean_visibility("RIGHT_ANKLE")

    # In image coordinates, y=0 is top.
    # At mid-swing, foot is lifted (y is minimum -> -y is peak).
    # At ground contact, foot is lowest (y is maximum).
    chosen_signal = None
    chosen_side = "left"

    if left_vis >= 0.4 and len(left_ankle_y) > 0 and not np.all(np.isnan(left_ankle_y)):
        chosen_signal = -left_ankle_y
        chosen_side = "left"
    elif right_vis >= 0.4 and len(right_ankle_y) > 0 and not np.all(np.isnan(right_ankle_y)):
        chosen_signal = -right_ankle_y
        chosen_side = "right"
    else:
        # Fallback to knee flexion or hip
        l_knee_y = tracker.get_trajectory("LEFT_KNEE", "y", smoothed=True)
        r_knee_y = tracker.get_trajectory("RIGHT_KNEE", "y", smoothed=True)
        if len(l_knee_y) > 0 and tracker.get_mean_visibility("LEFT_KNEE") >= 0.4:
            chosen_signal = -l_knee_y
            chosen_side = "left_knee"
            result.method = "knee_trajectory"
            result.notes.append("Ankle occluded; used knee trajectory for gait tracking.")
        elif len(r_knee_y) > 0 and tracker.get_mean_visibility("RIGHT_KNEE") >= 0.4:
            chosen_signal = -r_knee_y
            chosen_side = "right_knee"
            result.method = "knee_trajectory"
            result.notes.append("Ankle occluded; used knee trajectory for gait tracking.")
        else:
            hip_y = tracker.get_trajectory("LEFT_HIP", "y", smoothed=True)
            if len(hip_y) > 0:
                chosen_signal = -hip_y
                chosen_side = "hip"
                result.method = "hip_oscillation"
                result.notes.append("Used hip vertical oscillation for periodic gait tracking.")
            else:
                result.notes.append("Key lower-body landmarks not sufficiently visible.")
                return result

    signal = np.nan_to_num(chosen_signal, nan=0.0)
    sig_std = float(np.std(signal))

    if sig_std < 1e-4:
        result.notes.append("Insufficient kinematic movement detected in frame sequence.")
        return result

    # Periodicity check via FFT (0.7 Hz to 4.0 Hz = 42 to 240 SPM per step)
    fft_cycle_len = _fft_cycle_estimate(signal, fps)

    # Minimum distance between full gait cycles (typically 0.45s to 1.5s per full cycle)
    if fft_cycle_len and fft_cycle_len >= int(fps * 0.4):
        min_dist = max(int(fps * 0.35), int(fft_cycle_len * 0.75))
    else:
        min_dist = max(5, int(fps * 0.45))

    prominence = max(0.003, sig_std * 0.35)
    peaks, props = find_peaks(signal, distance=min_dist, prominence=prominence)

    if len(peaks) < MIN_CYCLES + 1:
        # Retry with lower prominence if periodic motion is subtle
        prominence_low = max(0.001, sig_std * 0.2)
        peaks, props = find_peaks(signal, distance=max(5, int(fps * 0.35)), prominence=prominence_low)

    if len(peaks) < MIN_CYCLES + 1:
        result.confidence = 0.1
        result.confidence_label = "Low"
        result.notes.append("Insufficient periodic cycles detected. Ensure side-view full-body visibility.")
        return result

    # Build cycle boundaries between consecutive swing peaks
    cycles: List[GaitCycle] = []
    timestamps = tracker.timestamps

    for i in range(len(peaks) - 1):
        s_frame = int(peaks[i])
        e_frame = int(peaks[i + 1])
        s_time = float(timestamps[s_frame]) if s_frame < len(timestamps) else s_frame / fps
        e_time = float(timestamps[e_frame]) if e_frame < len(timestamps) else e_frame / fps
        duration = e_time - s_time

        # Biomechanically plausible full gait cycle (0.4s to 1.8s)
        if duration < 0.35 or duration > 2.0:
            continue

        prom_val = float(props["prominences"][i]) if "prominences" in props and i < len(props["prominences"]) else sig_std
        cycle_conf = min(1.0, max(0.1, prom_val / max(sig_std, 1e-6)))

        cycles.append(GaitCycle(
            index=len(cycles) + 1,
            start_frame=s_frame,
            end_frame=e_frame,
            start_time_s=round(s_time, 2),
            end_time_s=round(e_time, 2),
            duration_s=round(duration, 3),
            confidence=round(cycle_conf, 2),
        ))

    if len(cycles) < MIN_CYCLES:
        result.notes.append("Too few physiologically valid running cycles detected.")
        return result

    durations = np.array([c.duration_s for c in cycles])
    mean_dur = float(np.mean(durations))
    std_dur = float(np.std(durations))

    # Cadence calculation: 1 full cycle (2 steps) -> SPM = 120 / mean_duration
    cadence = (2.0 * 60.0) / mean_dur if mean_dur > 0 else None

    # Autocorrelation confidence
    ac_conf = _autocorrelation_confidence(signal, int(mean_dur * fps))

    # Consistency of cycle durations (lower CV = higher confidence)
    cv = std_dur / mean_dur if mean_dur > 0 else 1.0
    cv_conf = max(0.0, 1.0 - cv * 2.5)

    # Visibility factor
    vis_score = max(left_vis, right_vis)
    overall_conf = float(np.clip((ac_conf * 0.4 + cv_conf * 0.4 + vis_score * 0.2), 0.05, 0.98))
    conf_label = "High" if overall_conf >= 0.70 else "Medium" if overall_conf >= 0.40 else "Low"

    for c in cycles:
        c.confidence = round(min(1.0, c.confidence * overall_conf), 2)

    result.cycles = cycles
    result.cadence_spm = round(cadence, 1) if cadence else None
    result.cycle_duration_mean_s = round(mean_dur, 3)
    result.cycle_duration_std_s = round(std_dur, 3)
    result.confidence = round(overall_conf, 2)
    result.confidence_label = conf_label

    logger.info(f"Gait cycles: {len(cycles)} detected, cadence={cadence:.1f} SPM, conf={overall_conf:.2f} ({conf_label})")
    return result


def _fft_cycle_estimate(signal: np.ndarray, fps: float) -> Optional[float]:
    """Estimate dominant stride frequency via FFT."""
    try:
        n = len(signal)
        if n < 16:
            return None
        yf = np.abs(fft(signal - np.mean(signal)))
        xf = fftfreq(n, 1.0 / fps)
        # Running frequency range: 0.6 Hz to 3.5 Hz
        mask = (xf >= 0.6) & (xf <= 3.5)
        if not np.any(mask):
            return None
        dominant_hz = float(xf[mask][np.argmax(yf[mask])])
        if dominant_hz <= 0:
            return None
        return fps / dominant_hz  # frames per full cycle
    except Exception:
        return None


def _autocorrelation_confidence(signal: np.ndarray, period_frames: int) -> float:
    """Measure signal periodicity using normalized autocorrelation at lag = period."""
    try:
        if period_frames <= 2 or period_frames >= len(signal) - 2:
            return 0.5
        sig_centered = signal - np.mean(signal)
        denom = float(np.sum(sig_centered ** 2))
        if denom < 1e-9:
            return 0.2
        ac = correlate(sig_centered, sig_centered, mode="full")
        ac = ac[len(ac) // 2:] / denom
        if period_frames < len(ac):
            # Peak near expected lag
            window = ac[max(0, period_frames - 3):min(len(ac), period_frames + 4)]
            if len(window) > 0:
                return float(np.clip(np.max(window), 0.0, 1.0))
        return 0.5
    except Exception:
        return 0.5
