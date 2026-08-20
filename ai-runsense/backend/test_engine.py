import os
import json
import numpy as np

from app.cv.video_validator import validate_video
from app.cv.pose_estimator import PoseEstimator
from app.cv.video_processor import process_video
from app.biomechanics.temporal_tracker import TemporalTracker
from app.biomechanics.gait_cycle import detect_gait_cycles
from app.biomechanics.metrics_engine import compute_metrics
from app.biomechanics.personal_baseline import compute_personal_baseline, compute_deviations
from app.biomechanics.fatigue_detector import detect_fatigue
from app.biomechanics.loading_index import compute_loading_index
from app.classification.style_classifier import classify_style
from app.classification.mistake_detector import detect_mistakes
from app.services.analysis_service import _compute_efficiency_score, _report_to_dict

test_video = "data/uploads/session_1_5d696279.mp4"
if not os.path.exists(test_video):
    # Try any available video
    uploads = [os.path.join("data/uploads", f) for f in os.listdir("data/uploads") if f.endswith(".mp4")]
    if uploads:
        test_video = uploads[0]

print(f"=== TESTING ANALYSIS ENGINE ON: {test_video} ===")
val = validate_video(test_video)
print(f"Video validation: valid={val.valid}, duration={val.duration_s:.2f}s, fps={val.fps:.1f}, {val.width}x{val.height}")

import cv2
cap = cv2.VideoCapture(test_video)
estimator = PoseEstimator(model_complexity=1)
all_landmarks = []
frame_idx = 0
fps = val.fps or 30.0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    fl = estimator.process_frame(frame, frame_idx, frame_idx / fps)
    all_landmarks.append(fl)
    frame_idx += 1
    if frame_idx >= 300:  # test 10 seconds of frames
        break
cap.release()
estimator.close()
print(f"Pose estimation: extracted landmarks for {len(all_landmarks)} frames")

tracker = TemporalTracker(all_landmarks)
gait = detect_gait_cycles(tracker, fps)
print(f"Gait cycles detected: {len(gait.cycles)}, Cadence: {gait.cadence_spm} SPM (conf={gait.confidence:.2f}, label={gait.confidence_label})")

report = compute_metrics(tracker, gait, fps, n_windows=10)
print("\n--- BIOMECHANICAL METRICS ---")
print("Cadence:", report.cadence.value if report.cadence else None, report.cadence.unit if report.cadence else "")
print("Stride Normalized:", report.stride_normalized.value if report.stride_normalized else None)
print("Vertical Oscillation:", report.vertical_oscillation.value if report.vertical_oscillation else None)
print("Symmetry Index:", report.symmetry_index.value if report.symmetry_index else None)
print("Trunk Lean:", report.trunk_lean.value if report.trunk_lean else None, "deg")
print("Left Knee Angle:", report.knee_angle_left.value if report.knee_angle_left else None, "deg")
print("Right Knee Angle:", report.knee_angle_right.value if report.knee_angle_right else None, "deg")
print("Arm Swing:", report.arm_swing.value if report.arm_swing else None, "deg")
print("Ground Contact Proxy:", report.ground_contact_estimate.value if report.ground_contact_estimate else None, "%")
print("Foot Strike:", report.foot_strike)
print("Pelvic Stability:", report.pelvic_stability.value if report.pelvic_stability else None)
print("Rhythm Score:", report.rhythm_score.value if report.rhythm_score else None)
print("Windows Count:", len(report.windows))

baseline = compute_personal_baseline(report, duration_s=frame_idx/fps)
print("\n--- PERSONAL BASELINE ---")
print("Baseline Cadence:", baseline.cadence_spm)
print("Baseline Symmetry:", baseline.symmetry)
print("Baseline Vertical Osc:", baseline.vertical_osc)
print("Baseline Windows:", baseline.baseline_windows, "of", baseline.total_windows)

deviations = compute_deviations(report.windows, baseline)
fatigue = detect_fatigue(deviations, duration_s=frame_idx/fps)
print("\n--- FATIGUE ANALYSIS ---")
print("Fatigue Detected:", fatigue.detected, "Confidence:", fatigue.confidence)
print("Onset Time:", fatigue.onset_time_s)
print("Drifting Metrics:", [d.name for d in fatigue.drifting_metrics])
print("Summary:", fatigue.summary)

style = classify_style(report)
print("\n--- STYLE DNA ---")
print("Primary Style:", style.primary_style, "Confidence:", style.confidence)
print("Secondary Style:", style.secondary_style)
print("Dimensions:", style.to_dict())

mistakes = detect_mistakes(report, gait, baseline, duration_s=frame_idx/fps)
print(f"\n--- MISTAKES DETECTED ({len(mistakes)}) ---")
for m in mistakes:
    print(f"[{m.severity.upper()}] {m.name} (conf={m.confidence:.2f}, ts={m.timestamp_s}s, frame={m.frame_number})")
    print(f"   Evidence: {m.evidence}")

loading = compute_loading_index(report, weight_kg=70.0)
print(f"\n--- LOADING INDEX ---")
print(f"Loading Index: {loading.index:.1f}/100 ({loading.level})")

efficiency = _compute_efficiency_score(report, style)
print(f"\n--- EFFICIENCY SCORE ---")
print(f"Overall Efficiency: {efficiency['overall']}/100, Components: {efficiency['components']}")

# Verify JSON serializability
metrics_dict = _report_to_dict(report)
json_test = json.dumps(metrics_dict)
print("\nJSON Serialization: SUCCESS! Length:", len(json_test))
print("=== VERIFICATION PASSED WITH ZERO ERRORS ===")
