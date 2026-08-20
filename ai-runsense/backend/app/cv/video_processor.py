"""
Video processor: reads every frame, runs pose estimation,
saves annotated video variants (pose overlay + analysis mode) with browser-compatible H.264 encoding.
Returns list of FrameLandmarks for downstream biomechanics.
"""
from __future__ import annotations
import logging
import os
from typing import List, Callable, Optional, Dict, Any

import cv2
import numpy as np

from app.cv.pose_estimator import PoseEstimator, FrameLandmarks
from app.cv.video_converter import convert_to_web_h264, is_web_compatible

logger = logging.getLogger(__name__)

PROCESS_EVERY_N = 1   # process every frame


def _create_video_writer(out_path: str, fps: float, w: int, h: int) -> cv2.VideoWriter:
    """
    Create a VideoWriter with browser-compatible H.264 / AVC1 codec.
    Tries Windows Media Foundation (CAP_MSMF) hardware encoder first, then standard fallbacks.
    """
    # 1. Windows Media Foundation H.264 (hardware accelerated, HTML5 native)
    try:
        fourcc = cv2.VideoWriter_fourcc(*"H264")
        writer = cv2.VideoWriter(out_path, cv2.CAP_MSMF, fourcc, fps, (w, h))
        if writer.isOpened():
            return writer
    except Exception:
        pass

    # 2. CAP_MSMF with avc1
    try:
        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        writer = cv2.VideoWriter(out_path, cv2.CAP_MSMF, fourcc, fps, (w, h))
        if writer.isOpened():
            return writer
    except Exception:
        pass

    # 3. Default backend with avc1
    try:
        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
        if writer.isOpened():
            return writer
    except Exception:
        pass

    # 4. Fallback mp4v
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    return cv2.VideoWriter(out_path, fourcc, fps, (w, h))


def process_video(
    input_path: str,
    output_dir: str,
    session_id: int,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    mistake_timestamps: Optional[Dict[float, Dict[str, Any]]] = None,
) -> List[FrameLandmarks]:
    """
    Full video processing pass:
    1. Read all frames
    2. Run MediaPipe Pose on each
    3. Save pose-overlay MP4 to output_dir
    4. Return list of FrameLandmarks
    """
    os.makedirs(output_dir, exist_ok=True)
    pose_out_path = os.path.join(output_dir, f"session_{session_id}_pose.mp4")
    analysis_out_path = os.path.join(output_dir, f"session_{session_id}_analysis.mp4")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    pose_writer = _create_video_writer(pose_out_path, fps, w, h)
    analysis_writer = _create_video_writer(analysis_out_path, fps, w, h)

    estimator = PoseEstimator(model_complexity=1)
    all_landmarks: List[FrameLandmarks] = []

    frame_idx = 0
    processed = 0

    if progress_callback:
        progress_callback(0.0, "Starting pose estimation…")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        timestamp_s = frame_idx / fps

        if frame_idx % PROCESS_EVERY_N == 0:
            fl = estimator.process_frame(frame, frame_idx, timestamp_s)
            all_landmarks.append(fl)
            processed += 1

            # Pose overlay frame
            pose_frame = estimator.draw_pose_overlay(frame, fl)
            pose_writer.write(pose_frame)

            # Analysis overlay frame
            mistake_info = _find_nearby_mistake(timestamp_s, mistake_timestamps or {})
            analysis_frame = estimator.draw_pose_overlay(
                frame, fl,
                highlight_joints=mistake_info.get("highlight_joints") if mistake_info else None,
                show_angles=True,
                mistake_label=mistake_info.get("label") if mistake_info else None,
            )
            analysis_writer.write(analysis_frame)
        else:
            pose_writer.write(frame)
            analysis_writer.write(frame)

        frame_idx += 1

        if progress_callback and frame_idx % 30 == 0:
            pct = min(90.0, (frame_idx / max(total_frames, 1)) * 90)
            progress_callback(pct, f"Processing frame {frame_idx}/{total_frames}…")

    cap.release()
    pose_writer.release()
    analysis_writer.release()
    estimator.close()

    if progress_callback:
        progress_callback(92.0, "Pose estimation complete.")

    # Convert raw OpenCV output to browser-compatible H.264+faststart
    # OpenCV MSMF writes moov at end of file — browsers cannot play these
    if progress_callback:
        progress_callback(93.0, "Converting pose video for browser…")
    _convert_inplace(pose_out_path)

    if progress_callback:
        progress_callback(96.0, "Converting analysis video for browser…")
    _convert_inplace(analysis_out_path)

    if progress_callback:
        progress_callback(99.0, "Video conversion complete.")

    logger.info(f"Processed {processed} frames from {input_path}")
    return all_landmarks


def _find_nearby_mistake(ts: float, mistake_map: Dict[float, Dict]) -> Optional[Dict]:
    """Return mistake annotation if within 0.5s of a known mistake timestamp."""
    for mts, info in mistake_map.items():
        if abs(ts - mts) <= 0.5:
            return info
    return None


def _convert_inplace(path: str) -> None:
    """
    Convert a video file to browser-compatible H.264+faststart in-place.
    Skips conversion if the file is already web-compatible (moov before mdat).
    """
    if not os.path.exists(path):
        return
    if is_web_compatible(path):
        logger.debug(f"{path} already web-compatible, skipping conversion")
        return
    tmp = path + ".converting.mp4"
    ok = convert_to_web_h264(path, tmp)
    if ok and os.path.exists(tmp):
        os.replace(tmp, path)
        logger.info(f"In-place conversion complete: {path}")
    else:
        if os.path.exists(tmp):
            os.remove(tmp)
        logger.warning(f"In-place conversion failed for {path}, keeping original")

def rewrite_analysis_video(
    input_path: str,
    output_dir: str,
    session_id: int,
    all_landmarks: List[FrameLandmarks],
    mistake_timestamps: Dict[float, Dict[str, Any]],
) -> str:
    """
    Second-pass: rewrite the analysis video with mistake annotations using H.264 writer.
    """
    analysis_out_path = os.path.join(output_dir, f"session_{session_id}_analysis.mp4")
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = _create_video_writer(analysis_out_path, fps, w, h)

    lm_by_frame = {fl.frame_number: fl for fl in all_landmarks}
    estimator = PoseEstimator(model_complexity=0)
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        ts = frame_idx / fps
        fl = lm_by_frame.get(frame_idx)
        if fl:
            mistake_info = _find_nearby_mistake(ts, mistake_timestamps)
            annotated = estimator.draw_pose_overlay(
                frame, fl,
                highlight_joints=mistake_info.get("highlight_joints") if mistake_info else None,
                show_angles=True,
                mistake_label=mistake_info.get("label") if mistake_info else None,
            )
            writer.write(annotated)
        else:
            writer.write(frame)
        frame_idx += 1

    cap.release()
    writer.release()
    estimator.close()
    _convert_inplace(analysis_out_path)
    return analysis_out_path
