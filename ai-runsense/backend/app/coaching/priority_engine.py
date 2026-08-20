"""
Priority Coach Engine.
Ranks detected mistakes using a transparent multi-factor model.
Returns top N ranked priorities with full explanations.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

import numpy as np

from app.classification.mistake_detector import Mistake, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {SEVERITY_HIGH: 1.0, SEVERITY_MEDIUM: 0.65, SEVERITY_LOW: 0.35}

# Context multipliers: how much each mistake type matters per running goal
GOAL_WEIGHTS: Dict[str, Dict[str, float]] = {
    "Improve Speed": {
        "Low Cadence": 1.4, "Over-Striding Pattern": 1.3, "Poor Arm Swing (Restricted)": 1.2,
    },
    "Improve Efficiency": {
        "Excessive Vertical Movement": 1.4, "Low Cadence": 1.3, "Over-Striding Pattern": 1.2,
    },
    "Injury Prevention": {
        "Pelvic Instability": 1.5, "Movement Asymmetry": 1.5, "Over-Striding Pattern": 1.3,
        "Excessive Trunk Lean": 1.3,
    },
    "Improve Technique": {
        "Cadence Instability": 1.3, "Poor Arm Swing (Over-Extended)": 1.2,
        "Poor Arm Swing (Restricted)": 1.2,
    },
}


@dataclass
class Priority:
    rank: int
    mistake: Mistake
    priority_score: float
    selected_reason: str
    focus_tip: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "name": self.mistake.name,
            "severity": self.mistake.severity,
            "confidence": self.mistake.confidence,
            "priority_score": round(self.priority_score, 2),
            "evidence": self.mistake.evidence,
            "timestamp_s": self.mistake.timestamp_s,
            "frame_number": self.mistake.frame_number,
            "relevant_metrics": self.mistake.relevant_metrics,
            "possible_effect": self.mistake.possible_effect,
            "suggested_correction": self.mistake.suggested_correction,
            "selected_reason": self.selected_reason,
            "focus_tip": self.focus_tip,
            "highlight_joints": self.mistake.highlight_joints,
            "id": self.mistake.id,
        }


def compute_priorities(
    mistakes: List[Mistake],
    session_goal: Optional[str] = None,
    top_n: int = 3,
) -> List[Priority]:
    """Rank mistakes and return the top N priorities."""
    if not mistakes:
        return []

    goal_map = GOAL_WEIGHTS.get(session_goal or "", {})
    scored = []

    for m in mistakes:
        sev_weight = SEVERITY_WEIGHTS.get(m.severity, 0.5)
        goal_mult = goal_map.get(m.name, 1.0)
        score = sev_weight * m.confidence * goal_mult * 100
        scored.append((score, m))

    scored.sort(key=lambda x: -x[0])
    top = scored[:top_n]

    priorities = []
    for i, (score, m) in enumerate(top):
        reason = _build_reason(m, session_goal, goal_map.get(m.name, 1.0))
        tip = _build_focus_tip(m)
        priorities.append(Priority(
            rank=i + 1,
            mistake=m,
            priority_score=score,
            selected_reason=reason,
            focus_tip=tip,
        ))

    logger.info(f"Priorities: {[p.mistake.name for p in priorities]}")
    return priorities


def _build_reason(m: Mistake, goal: Optional[str], goal_mult: float) -> str:
    parts = [f"Ranked as {_sev_label(m.severity)}-severity issue with {m.confidence * 100:.0f}% confidence."]
    if goal and goal_mult > 1.0:
        parts.append(f"Given your goal ({goal}), this issue is particularly relevant.")
    return " ".join(parts)


def _build_focus_tip(m: Mistake) -> str:
    tips = {
        "Low Cadence": "Try increasing cadence by 5–10 steps/min at a comfortable pace first.",
        "Over-Striding Pattern": "Land with your foot closer to below your hips, not in front.",
        "Excessive Vertical Movement": "Think 'forward, not up' on each push-off.",
        "Movement Asymmetry": "Pay equal attention to both sides during drills.",
        "Excessive Trunk Lean": "Run 'tall' — imagine a string pulling you upward from the crown of your head.",
        "Very Upright Posture": "Lean slightly forward from the ankles, maintaining a neutral spine.",
        "Poor Arm Swing (Over-Extended)": "Drive elbows back, not arms forward, and keep them bent.",
        "Poor Arm Swing (Restricted)": "Relax your hands and allow arms to swing freely.",
        "Pelvic Instability": "Single-leg exercises (bridges, step-ups) can improve hip stability.",
        "Cadence Instability": "Use a consistent-tempo playlist or metronome to anchor your rhythm.",
    }
    return tips.get(m.name, m.suggested_correction[:120] + "…" if len(m.suggested_correction) > 120 else m.suggested_correction)


def _sev_label(s: str) -> str:
    return {"high": "HIGH", "medium": "MEDIUM", "low": "LOW"}.get(s, s.upper())
