"""
Video validation before processing.
Checks duration, frame count, pose detectability, body visibility.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import List, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

MIN_DURATION_S = 3.0
MIN_FRAMES = 30
MIN_POSE_CONFIDENCE = 0.4
SAMPLE_FRAME_COUNT = 10   # frames to sample for quick validation


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]
    duration_s: float = 0.0
    fps: float = 0.0
    frame_count: int = 0
    width: int = 0
    height: int = 0
    pose_detected_ratio: float = 0.0
    mean_confidence: float = 0.0


def validate_video(path: str) -> ValidationResult:
    """
    Run pre-processing validation on a video file.
    Returns a ValidationResult with errors/warnings and metadata.
    """
    errors: List[str] = []
    warnings: List[str] = []

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return ValidationResult(valid=False, errors=["Could not open video file. Ensure it is a supported format (MP4, MOV, AVI)."], warnings=[])

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_s = frame_count / fps if fps > 0 else 0.0

    if duration_s < MIN_DURATION_S:
        errors.append(f"Video is too short ({duration_s:.1f}s). Minimum is {MIN_DURATION_S}s.")
    if frame_count < MIN_FRAMES:
        errors.append(f"Insufficient frames ({frame_count}). Minimum is {MIN_FRAMES}.")
    if width < 320 or height < 240:
        warnings.append(f"Low resolution ({width}×{height}). Higher resolution improves analysis accuracy.")
    if fps < 15:
        warnings.append(f"Low frame rate ({fps:.1f} fps). At least 24 fps recommended for reliable gait-cycle detection.")

    # Quick pose check on sampled frames
    pose_detected = 0
    confidences = []

    if frame_count > 0 and not errors:
        try:
            import mediapipe as mp
            mp_pose = mp.solutions.pose
            pose = mp_pose.Pose(
                static_image_mode=True,
                model_complexity=0,
                min_detection_confidence=MIN_POSE_CONFIDENCE,
            )
            step = max(1, frame_count // SAMPLE_FRAME_COUNT)
            sampled = 0
            for i in range(0, frame_count, step):
                if sampled >= SAMPLE_FRAME_COUNT:
                    break
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if not ret:
                    continue
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = pose.process(rgb)
                sampled += 1
                if result.pose_landmarks:
                    pose_detected += 1
                    vis = [lm.visibility for lm in result.pose_landmarks.landmark]
                    confidences.append(float(np.mean(vis)))
            pose.close()
        except Exception as e:
            warnings.append(f"Pose pre-check failed: {e}. Analysis will still attempt to run.")

    pose_ratio = pose_detected / SAMPLE_FRAME_COUNT if SAMPLE_FRAME_COUNT > 0 else 0.0
    mean_conf = float(np.mean(confidences)) if confidences else 0.0

    if pose_ratio < 0.3:
        errors.append("Runner body could not be reliably detected in sampled frames. Ensure the full body is visible and lighting is adequate.")
    elif pose_ratio < 0.6:
        warnings.append("Runner detection confidence is low. Some metrics may be unavailable or marked as low-confidence.")

    cap.release()

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        duration_s=duration_s,
        fps=fps,
        frame_count=frame_count,
        width=width,
        height=height,
        pose_detected_ratio=pose_ratio,
        mean_confidence=mean_conf,
    )
