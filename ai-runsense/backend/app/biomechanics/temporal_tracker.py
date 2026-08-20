"""
Temporal tracker: converts raw FrameLandmarks into smoothed trajectories.
Applies Savitzky-Golay filter to reduce noise while preserving gait events.
"""
from __future__ import annotations
import logging
from typing import List, Dict, Optional

import numpy as np
from scipy.signal import savgol_filter

from app.cv.pose_estimator import FrameLandmarks

logger = logging.getLogger(__name__)

SAVGOL_WINDOW = 11   # must be odd; ~0.37s at 30fps
SAVGOL_POLY = 3
MIN_VISIBILITY = 0.3


class TemporalTracker:
    """
    Maintains smoothed per-landmark trajectories over time.
    Access trajectories via .get_trajectory(landmark_name, axis).
    """

    def __init__(self, frames: List[FrameLandmarks]):
        self.frames = frames
        self._trajectories: Dict[str, Dict[str, np.ndarray]] = {}
        self.timestamps = np.array([f.timestamp_s for f in frames])
        self.frame_numbers = np.array([f.frame_number for f in frames])
        self._build()

    def _build(self):
        """Build raw + smoothed trajectories for all key landmarks."""
        if not self.frames:
            return

        # Collect all landmark names
        lm_names = set()
        for f in self.frames:
            lm_names.update(f.landmarks.keys())

        for name in lm_names:
            xs, ys, zs, vis = [], [], [], []
            for f in self.frames:
                lm = f.landmarks.get(name)
                if lm:
                    xs.append(lm["x"])
                    ys.append(lm["y"])
                    zs.append(lm["z"])
                    vis.append(lm["visibility"])
                else:
                    xs.append(np.nan)
                    ys.append(np.nan)
                    zs.append(np.nan)
                    vis.append(0.0)

            xs = np.array(xs, dtype=float)
            ys = np.array(ys, dtype=float)
            zs = np.array(zs, dtype=float)
            vis = np.array(vis, dtype=float)

            # Interpolate short NaN gaps (up to 5 frames)
            xs = _interp_nans(xs, max_gap=5)
            ys = _interp_nans(ys, max_gap=5)

            # Apply Savitzky-Golay smoothing
            n = len(xs)
            window = min(SAVGOL_WINDOW, n if n % 2 == 1 else n - 1)
            if window >= 5 and not np.all(np.isnan(xs)):
                try:
                    xs_smooth = savgol_filter(np.nan_to_num(xs), window, SAVGOL_POLY)
                    ys_smooth = savgol_filter(np.nan_to_num(ys), window, SAVGOL_POLY)
                except Exception:
                    xs_smooth, ys_smooth = xs.copy(), ys.copy()
            else:
                xs_smooth, ys_smooth = xs.copy(), ys.copy()

            self._trajectories[name] = {
                "x": xs, "y": ys, "z": zs, "visibility": vis,
                "x_smooth": xs_smooth, "y_smooth": ys_smooth,
            }

    def get_trajectory(self, landmark: str, axis: str = "y", smoothed: bool = True) -> np.ndarray:
        """Return 1D time series for a landmark axis."""
        traj = self._trajectories.get(landmark, {})
        key = f"{axis}_smooth" if smoothed and f"{axis}_smooth" in traj else axis
        return traj.get(key, np.array([]))

    def get_visibility(self, landmark: str) -> np.ndarray:
        return self._trajectories.get(landmark, {}).get("visibility", np.array([]))

    def get_mean_visibility(self, landmark: str) -> float:
        vis = self.get_visibility(landmark)
        valid = vis[vis > MIN_VISIBILITY]
        return float(np.mean(valid)) if len(valid) > 0 else 0.0

    def get_landmark_at_frame(self, landmark: str, frame_idx: int) -> Optional[Dict[str, float]]:
        traj = self._trajectories.get(landmark)
        if traj is None or frame_idx >= len(traj["x"]):
            return None
        return {
            "x": traj["x_smooth"][frame_idx] if "x_smooth" in traj else traj["x"][frame_idx],
            "y": traj["y_smooth"][frame_idx] if "y_smooth" in traj else traj["y"][frame_idx],
            "z": traj["z"][frame_idx],
            "visibility": traj["visibility"][frame_idx],
        }

    @property
    def n_frames(self) -> int:
        return len(self.frames)

    @property
    def duration_s(self) -> float:
        return float(self.timestamps[-1]) if len(self.timestamps) > 0 else 0.0


def _interp_nans(arr: np.ndarray, max_gap: int = 5) -> np.ndarray:
    """Linear interpolation for NaN gaps up to max_gap frames."""
    result = arr.copy()
    nan_mask = np.isnan(result)
    if not np.any(nan_mask):
        return result

    indices = np.arange(len(result))
    # Find runs of NaN
    in_gap = False
    gap_start = 0
    for i, is_nan in enumerate(nan_mask):
        if is_nan and not in_gap:
            in_gap = True
            gap_start = i
        elif not is_nan and in_gap:
            gap_len = i - gap_start
            if gap_len <= max_gap and gap_start > 0:
                # Interpolate
                v0 = result[gap_start - 1]
                v1 = result[i]
                for j in range(gap_len):
                    result[gap_start + j] = v0 + (v1 - v0) * (j + 1) / (gap_len + 1)
            in_gap = False

    return result
