"""
MediaPipe Pose wrapper.
Extracts per-frame landmarks, computes confidence, draws skeleton overlays.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict

import cv2
import numpy as np
import mediapipe as mp

logger = logging.getLogger(__name__)

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# MediaPipe landmark indices
LM = mp_pose.PoseLandmark

# Groups used in analysis
JOINT_GROUPS = {
    "left_arm": [LM.LEFT_SHOULDER, LM.LEFT_ELBOW, LM.LEFT_WRIST],
    "right_arm": [LM.RIGHT_SHOULDER, LM.RIGHT_ELBOW, LM.RIGHT_WRIST],
    "left_leg": [LM.LEFT_HIP, LM.LEFT_KNEE, LM.LEFT_ANKLE],
    "right_leg": [LM.RIGHT_HIP, LM.RIGHT_KNEE, LM.RIGHT_ANKLE],
    "trunk": [LM.LEFT_SHOULDER, LM.RIGHT_SHOULDER, LM.LEFT_HIP, LM.RIGHT_HIP],
    "left_foot": [LM.LEFT_ANKLE, LM.LEFT_HEEL, LM.LEFT_FOOT_INDEX],
    "right_foot": [LM.RIGHT_ANKLE, LM.RIGHT_HEEL, LM.RIGHT_FOOT_INDEX],
}

KEY_LANDMARKS = [
    LM.NOSE,
    LM.LEFT_SHOULDER, LM.RIGHT_SHOULDER,
    LM.LEFT_ELBOW, LM.RIGHT_ELBOW,
    LM.LEFT_WRIST, LM.RIGHT_WRIST,
    LM.LEFT_HIP, LM.RIGHT_HIP,
    LM.LEFT_KNEE, LM.RIGHT_KNEE,
    LM.LEFT_ANKLE, LM.RIGHT_ANKLE,
    LM.LEFT_HEEL, LM.RIGHT_HEEL,
    LM.LEFT_FOOT_INDEX, LM.RIGHT_FOOT_INDEX,
]


@dataclass
class FrameLandmarks:
    frame_number: int
    timestamp_s: float
    landmarks: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # key: landmark name, value: {x, y, z, visibility}
    mean_confidence: float = 0.0
    pose_detected: bool = False


class PoseEstimator:
    def __init__(
        self,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        self.pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            enable_segmentation=False,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.model_complexity = model_complexity

    def process_frame(self, frame_bgr: np.ndarray, frame_number: int, timestamp_s: float) -> FrameLandmarks:
        """Run pose estimation on a single BGR frame."""
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        results = self.pose.process(frame_rgb)
        frame_rgb.flags.writeable = True

        fl = FrameLandmarks(frame_number=frame_number, timestamp_s=timestamp_s)

        if results.pose_landmarks:
            fl.pose_detected = True
            lm_list = results.pose_landmarks.landmark
            visibilities = []
            for lm_enum in KEY_LANDMARKS:
                lm = lm_list[lm_enum.value]
                fl.landmarks[lm_enum.name] = {
                    "x": lm.x,
                    "y": lm.y,
                    "z": lm.z,
                    "visibility": lm.visibility,
                }
                visibilities.append(lm.visibility)
            fl.mean_confidence = float(np.mean(visibilities)) if visibilities else 0.0

        return fl

    def draw_pose_overlay(
        self,
        frame_bgr: np.ndarray,
        frame_landmarks: FrameLandmarks,
        highlight_joints: Optional[List[str]] = None,
        show_angles: bool = False,
        angles: Optional[Dict[str, float]] = None,
        mistake_label: Optional[str] = None,
    ) -> np.ndarray:
        """Draw skeleton overlay onto a copy of the frame."""
        out = frame_bgr.copy()

        if not frame_landmarks.pose_detected:
            return out

        h, w = out.shape[:2]

        def px(name: str) -> Optional[Tuple[int, int]]:
            lm = frame_landmarks.landmarks.get(name)
            if lm and lm["visibility"] > 0.3:
                return (int(lm["x"] * w), int(lm["y"] * h))
            return None

        # Skeleton connections
        CONNECTIONS = [
            # Torso
            ("LEFT_SHOULDER", "RIGHT_SHOULDER"),
            ("LEFT_SHOULDER", "LEFT_HIP"),
            ("RIGHT_SHOULDER", "RIGHT_HIP"),
            ("LEFT_HIP", "RIGHT_HIP"),
            # Left arm
            ("LEFT_SHOULDER", "LEFT_ELBOW"),
            ("LEFT_ELBOW", "LEFT_WRIST"),
            # Right arm
            ("RIGHT_SHOULDER", "RIGHT_ELBOW"),
            ("RIGHT_ELBOW", "RIGHT_WRIST"),
            # Left leg
            ("LEFT_HIP", "LEFT_KNEE"),
            ("LEFT_KNEE", "LEFT_ANKLE"),
            ("LEFT_ANKLE", "LEFT_HEEL"),
            ("LEFT_ANKLE", "LEFT_FOOT_INDEX"),
            # Right leg
            ("RIGHT_HIP", "RIGHT_KNEE"),
            ("RIGHT_KNEE", "RIGHT_ANKLE"),
            ("RIGHT_ANKLE", "RIGHT_HEEL"),
            ("RIGHT_ANKLE", "RIGHT_FOOT_INDEX"),
            # Head
            ("NOSE", "LEFT_SHOULDER"),
            ("NOSE", "RIGHT_SHOULDER"),
        ]

        highlight_set = set(highlight_joints or [])

        # Draw connections
        for a, b in CONNECTIONS:
            pa, pb = px(a), px(b)
            if pa and pb:
                color = (0, 255, 120)  # neon green default
                thickness = 2
                if a in highlight_set or b in highlight_set:
                    color = (0, 100, 255)   # orange-red for highlighted
                    thickness = 3
                cv2.line(out, pa, pb, color, thickness, cv2.LINE_AA)

        # Draw joints and joint name annotations
        for name, lm in frame_landmarks.landmarks.items():
            p = px(name)
            if p:
                is_highlighted = name in highlight_set
                color = (0, 140, 255) if is_highlighted else (0, 240, 255)  # orange-red vs cyan
                radius = 7 if is_highlighted else 4
                cv2.circle(out, p, radius, color, -1, cv2.LINE_AA)
                cv2.circle(out, p, radius + 2, (0, 0, 0), 1, cv2.LINE_AA)

                # If joint is in highlight set, annotate joint text message clearly
                if is_highlighted:
                    clean_name = name.replace("_", " ").title()
                    label_text = f"{clean_name}"
                    (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                    tx, ty = p[0] + 10, p[1] - 8
                    # Background pill
                    cv2.rectangle(out, (tx - 3, ty - th - 3), (tx + tw + 3, ty + 3), (20, 20, 20), -1)
                    cv2.rectangle(out, (tx - 3, ty - th - 3), (tx + tw + 3, ty + 3), (0, 140, 255), 1)
                    cv2.putText(out, label_text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        # Body center estimate (midpoint of hips)
        lh = px("LEFT_HIP")
        rh = px("RIGHT_HIP")
        if lh and rh:
            cx = (lh[0] + rh[0]) // 2
            cy = (lh[1] + rh[1]) // 2
            cv2.circle(out, (cx, cy), 6, (255, 50, 200), -1, cv2.LINE_AA)
            cv2.circle(out, (cx, cy), 8, (255, 255, 255), 1, cv2.LINE_AA)
            (tw, th), _ = cv2.getTextSize("Center of Mass", cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.rectangle(out, (cx + 8, cy - th - 2), (cx + 10 + tw + 2, cy + 3), (20, 20, 20), -1)
            cv2.putText(out, "Center of Mass", (cx + 10, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 120, 230), 1, cv2.LINE_AA)

        # Draw angles with readable backdrop
        if show_angles and angles:
            for joint, angle in angles.items():
                joint_px = px(joint)
                if joint_px:
                    ang_text = f"{angle:.0f}°"
                    (tw, th), _ = cv2.getTextSize(ang_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                    ax, ay = joint_px[0] + 10, joint_px[1] + 14
                    cv2.rectangle(out, (ax - 2, ay - th - 2), (ax + tw + 2, ay + 2), (0, 0, 0), -1)
                    cv2.putText(out, ang_text, (ax, ay), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)

        # Mistake label overlay banner
        if mistake_label:
            overlay = out.copy()
            cv2.rectangle(overlay, (0, h - 56), (w, h), (15, 23, 42), -1)
            cv2.addWeighted(overlay, 0.85, out, 0.15, 0, out)
            # Red left accent
            cv2.rectangle(out, (0, h - 56), (6, h), (0, 100, 255), -1)
            cv2.putText(out, f"FORM DEVIATION: {mistake_label.upper()}", (18, h - 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(out, f"FORM DEVIATION: {mistake_label.upper()}", (18, h - 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 180, 255), 1, cv2.LINE_AA)

        # Confidence badge at top left
        conf_color = (0, 220, 100) if frame_landmarks.mean_confidence > 0.7 else (0, 190, 255) if frame_landmarks.mean_confidence > 0.5 else (60, 60, 255)
        badge_text = f"Pose Tracking: {int(frame_landmarks.mean_confidence * 100)}%"
        (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(out, (10, 8), (16 + tw, 14 + th + 4), (15, 23, 42), -1)
        cv2.rectangle(out, (10, 8), (16 + tw, 14 + th + 4), conf_color, 1)
        cv2.putText(out, badge_text, (13, 20 + th // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, conf_color, 1, cv2.LINE_AA)

        return out

    def close(self):
        self.pose.close()
