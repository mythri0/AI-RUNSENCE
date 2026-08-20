"""
AI Coach — generates evidence-grounded coaching narratives.
Primary: Google Gemini API (if GEMINI_API_KEY is set).
Fallback: Deterministic template engine — strictly uses real computed metrics.
Never fabricates metrics. Uses performance-oriented language without medical diagnoses.
"""
from __future__ import annotations
import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

_GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai  # type: ignore
    _GEMINI_AVAILABLE = True
except ImportError:
    pass


def generate_coaching(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a coaching narrative from structured analysis input.
    Never invent metrics — only use what is present in `analysis`.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if _GEMINI_AVAILABLE and api_key:
        try:
            return _gemini_coach(analysis, api_key)
        except Exception as e:
            logger.warning(f"Gemini coaching failed: {e}. Falling back to deterministic engine.")

    return _deterministic_coach(analysis)


# ─── Gemini Coach ─────────────────────────────────────────────────────────────

def _gemini_coach(analysis: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = _build_gemini_prompt(analysis)
    response = model.generate_content(prompt)
    text = response.text if hasattr(response, "text") else str(response)

    sections = _parse_gemini_sections(text)
    sections["generated_by"] = "gemini"
    return sections


def _build_gemini_prompt(analysis: Dict[str, Any]) -> str:
    metrics = analysis.get("metrics", {})
    baseline = analysis.get("baseline", {})
    mistakes = analysis.get("mistakes", [])
    priorities = analysis.get("priorities", [])
    fatigue = analysis.get("fatigue", {})
    style = analysis.get("style", {})
    context = analysis.get("context", {})
    runner = analysis.get("runner", {})
    history = analysis.get("history", [])

    top_p = priorities[0] if priorities else None
    top_name = top_p["name"] if top_p else "None"
    top_sev = top_p["severity"] if top_p else "N/A"

    mistake_summary = [f"{m['name']} ({m['severity']}, {m.get('evidence', '')})" for m in mistakes[:4]]
    drifting = [d["name"] for d in fatigue.get("drifting_metrics", [])]

    return f"""You are an evidence-grounded AI running coach for AI RunSense.

STRICT GUIDELINES:
1. Do NOT invent or assume any metric, score, or number not explicitly provided below.
2. If any metric is labeled as low confidence or estimated, acknowledge the uncertainty (e.g., "Camera-estimated", "Estimated indicator").
3. Use performance-oriented, encouraging coaching language. NEVER make medical diagnoses or clinical guarantees.
4. Base all recommendations and drill cues directly on the runner's actual measured numbers and context.

RUNNER PROFILE & CONTEXT:
* Experience: {runner.get('experience_level', 'Not specified')} | Age: {runner.get('age', 'Not specified')} | Goal: {runner.get('primary_goal', context.get('session_goal', 'General Fitness'))}
* Session Focus: {context.get('session_goal', 'Not specified')} | Distance: {context.get('distance_type', 'Not specified')} | Surface: {context.get('environment', 'Not specified')}
* Running Style DNA: {style.get('primary_style', 'Balanced Runner')} ({style.get('confidence', 0.5) * 100:.0f}% match)

MEASURED RUN BIOMECHANICS:
* Cadence: {metrics.get('cadence', {}).get('value', 'N/A')} SPM (Baseline: {baseline.get('cadence_spm', 'N/A')} SPM, Conf: {metrics.get('cadence', {}).get('confidence', 0.5)})
* Symmetry Index: {metrics.get('symmetry_index', {}).get('value', 'N/A')}/100 (Baseline: {baseline.get('symmetry', 'N/A')})
* Vertical Oscillation: {metrics.get('vertical_oscillation', {}).get('value', 'N/A')} ratio (Baseline: {baseline.get('vertical_osc', 'N/A')})
* Trunk Lean: {metrics.get('trunk_lean', {}).get('value', 'N/A')}°
* Arm Swing Flexion: {metrics.get('arm_swing', {}).get('value', 'N/A')}°
* Pelvic Stability: {metrics.get('pelvic_stability', {}).get('value', 'N/A')}/100
* Rhythm Consistency: {metrics.get('rhythm_score', {}).get('value', 'N/A')}/100

ISSUES & DEGRADATION:
* Top Priority Issue: {top_name} ({top_sev})
* Detected Issues: {'; '.join(mistake_summary) if mistake_summary else 'None'}
* Fatigue / Form Degradation: {fatigue.get('detected', False)} (Drifting: {', '.join(drifting) if drifting else 'None'})

Output exactly these 6 sections using markdown headers:
### Top Priority
(Specify the #1 focus area with exact measured evidence, the recommended specific drill, and a target metric for the next run)

### What You're Doing Well
(2-3 bullet points highlighting positive kinematic scores from the real data)

### What Changed
(2-3 bullet points comparing current metrics against baseline or early session slices)

### Why It May Matter
(2 bullet points explaining how these mechanics impact energy conservation or running economy)

### What To Focus On Next
(2-3 actionable cues and drills)

### Context-Specific Recommendation
(A tailored paragraph aligning their primary goal, surface, and distance)"""


def _parse_gemini_sections(text: str) -> Dict[str, Any]:
    section_keys = {
        "Top Priority": "top_priority",
        "What You're Doing Well": "doing_well",
        "What Changed": "what_changed",
        "Why It May Matter": "why_it_matters",
        "What To Focus On Next": "focus_next",
        "Context-Specific Recommendation": "context_recommendation",
    }

    result: Dict[str, Any] = {
        "doing_well": [], "what_changed": [], "why_it_matters": [],
        "top_priority": "", "focus_next": [], "context_recommendation": "",
    }

    current_key = None
    current_lines: List[str] = []

    for line in text.split("\n"):
        stripped = line.strip().lstrip("#").strip()
        matched = None
        for header, key in section_keys.items():
            if header.lower() in stripped.lower():
                matched = key
                break
        if matched:
            if current_key and current_lines:
                _set_section(result, current_key, current_lines)
            current_key = matched
            current_lines = []
        elif current_key and stripped:
            current_lines.append(stripped.lstrip("•-* "))

    if current_key and current_lines:
        _set_section(result, current_key, current_lines)

    return result


def _set_section(result: Dict, key: str, lines: List[str]):
    if key in ("top_priority", "context_recommendation"):
        result[key] = " ".join(lines)
    else:
        result[key] = [l for l in lines if l]


# ─── Deterministic Coach ──────────────────────────────────────────────────────

DRILL_MAP = {
    "Low Cadence": ("High Knees / Fast-Feet Turnover Drill", "Increase step frequency by 5–8 SPM at easy pace using a rhythmic metronome cue."),
    "Over-Striding Pattern": ("A-Skips & Paw-Back Drill", "Focus on landing with foot under center of gravity rather than reaching forward."),
    "Excessive Vertical Movement": ("Low-Ceiling / Glide Running Drills", "Direct energy horizontally forward, keeping hips level."),
    "Movement Asymmetry": ("Single-Leg Romanian Deadlifts & Step-Ups", "Build bilateral hip/glute balance to distribute load evenly."),
    "Excessive Trunk Lean": ("Wall Lean Alignment & Tall-Running Cues", "Run tall, initiating lean subtly from the ankles with neutral spine."),
    "Very Upright Posture": ("Ankle Hinge Lean Drill", "Allow a natural 5–10° forward lean to utilize gravity assist."),
    "Poor Arm Swing (Over-Extended)": ("Seated Arm Swing Drill (90° Elbows)", "Drive elbows back in compact 90° rhythm."),
    "Pelvic Instability": ("Lateral Band Walks & Side Planks", "Strengthen gluteus medius to eliminate single-leg pelvic drop."),
    "Cadence Instability": ("Metronome Running Intervals", "Anchor a steady stride frequency with rhythmic breathing (3:3 or 2:2)."),
}


def _deterministic_coach(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evidence-grounded deterministic coaching engine.
    Strictly binds advice to real metrics and calculated deviations.
    """
    metrics = analysis.get("metrics", {})
    baseline = analysis.get("baseline", {})
    mistakes = analysis.get("mistakes", [])
    priorities = analysis.get("priorities", [])
    fatigue = analysis.get("fatigue", {})
    style = analysis.get("style", {})
    context = analysis.get("context", {})
    runner = analysis.get("runner", {})

    doing_well = _doing_well_bullets(metrics, mistakes, style)
    what_changed = _what_changed_bullets(fatigue, baseline, metrics)
    why_matters = _why_matters_bullets(priorities, fatigue)
    top_priority = _top_priority_text(priorities, metrics, baseline)
    focus_next = _focus_next_bullets(priorities)
    context_rec = _context_recommendation(context, runner, priorities, fatigue)

    return {
        "doing_well": doing_well,
        "what_changed": what_changed,
        "why_it_matters": why_matters,
        "top_priority": top_priority,
        "focus_next": focus_next,
        "context_recommendation": context_rec,
        "generated_by": "deterministic",
    }


def _doing_well_bullets(metrics: Dict, mistakes: Dict, style: Dict) -> List[str]:
    bullets = []
    sym = _val(metrics, "symmetry_index")
    if sym and sym >= 80:
        bullets.append(f"Left-right kinematic symmetry is strong at {sym:.0f}/100, showing balanced bilateral mechanics.")
    rhythm = _val(metrics, "rhythm_score")
    if rhythm and rhythm >= 75:
        bullets.append(f"Stride rhythm consistency scored {rhythm:.0f}/100, indicating steady pacing.")
    cad = _val(metrics, "cadence")
    if cad and cad >= 168:
        bullets.append(f"Cadence turnover is solid at {cad:.0f} steps/min.")
    posture = _val(metrics, "trunk_lean")
    if posture and 5.0 <= posture <= 12.0:
        bullets.append(f"Trunk lean posture is within the efficient 5–12° window ({posture:.1f}°).")

    if not mistakes and not bullets:
        bullets.append("Form remained stable and consistent across the recorded session.")
    elif not bullets:
        bullets.append("Clear video landmarks were tracked to establish your initial movement profile.")
    return bullets[:3]


def _what_changed_bullets(fatigue: Dict, baseline: Dict, metrics: Dict) -> List[str]:
    bullets = []
    if fatigue.get("detected"):
        drifting = fatigue.get("drifting_metrics", [])
        names = ", ".join(d["name"] for d in drifting) if drifting else "Key kinematic metrics"
        onset = fatigue.get("onset_time_s")
        onset_str = f" starting around {_fmt_time(onset)}" if onset else ""
        bullets.append(f"Systematic form degradation detected{onset_str}: {names} exhibited progressive mechanical drift.")
    else:
        bullets.append("Movement mechanics remained stable with no sustained degradation across time windows.")

    cad_dev = _baseline_dev(baseline, "cadence_spm", metrics, "cadence")
    if cad_dev and abs(cad_dev) >= 3.0:
        direction = "lower than" if cad_dev < 0 else "higher than"
        bullets.append(f"Average cadence was {abs(cad_dev):.1f}% {direction} your initial baseline window ({baseline.get('cadence_spm', 0):.0f} SPM).")

    sym_dev = _baseline_dev(baseline, "symmetry", metrics, "symmetry_index")
    if sym_dev and abs(sym_dev) >= 4.0:
        direction = "dropped" if sym_dev < 0 else "improved"
        bullets.append(f"Symmetry {direction} by {abs(sym_dev):.1f}% relative to your early baseline.")

    return bullets[:3]


def _why_matters_bullets(priorities: List[Dict], fatigue: Dict) -> List[str]:
    bullets = []
    for p in priorities[:2]:
        bullets.append(f"{p['name']}: {p.get('possible_effect', '')}")
    if fatigue.get("detected") and len(bullets) < 3:
        bullets.append("Form deterioration late in runs increases metabolic cost and concentrates impact on fatiguing muscles.")
    if not bullets:
        bullets.append("Maintaining balanced mechanics minimizes braking forces and optimizes energy transfer.")
    return bullets[:3]


def _top_priority_text(priorities: List[Dict], metrics: Dict, baseline: Dict) -> str:
    if not priorities:
        return "No high-priority issues detected. Focus on maintaining current fluid mechanics and consistent pacing."

    p = priorities[0]
    name = p["name"]
    drill, cue = DRILL_MAP.get(name, ("Technique Drill", p.get("suggested_correction", "")))

    parts = [f"Primary Focus: {name} ({p['severity'].upper()} severity)."]
    if p.get("evidence"):
        parts.append(p["evidence"])
    parts.append(f"Recommended Drill: {drill}. Next-Run Target: {cue}")
    return " ".join(parts)


def _focus_next_bullets(priorities: List[Dict]) -> List[str]:
    if not priorities:
        return ["Maintain current rhythm and cadence turnover during tempo runs."]
    bullets = []
    for p in priorities[:3]:
        tip = p.get("focus_tip") or p.get("suggested_correction", "")
        drill, _ = DRILL_MAP.get(p["name"], ("", ""))
        if drill:
            bullets.append(f"{p['name']}: Practice {drill} — {tip}")
        else:
            bullets.append(f"{p['name']}: {tip}")
    return bullets


def _context_recommendation(context: Dict, runner: Dict, priorities: List[Dict], fatigue: Dict) -> str:
    goal = context.get("session_goal", runner.get("primary_goal", "General Fitness"))
    dist = context.get("distance_type", "mid_distance")
    exp = runner.get("experience_level", "intermediate")

    parts = [f"Tailored for your {exp} level and '{goal}' objective:"]
    if goal == "Improve Speed":
        parts.append("Speed gains come from quicker ground departure and high turnover rather than overstriding.")
    elif goal == "Improve Efficiency":
        parts.append("Efficiency hinges on minimizing vertical bounce and maintaining smooth rhythmic cadence.")
    elif goal == "Injury Prevention":
        parts.append("Focus on symmetry and pelvic control to keep joint loading balanced across both limbs.")
    else:
        parts.append("Aim for progressive, gradual adjustments over multiple training sessions.")

    if dist in ("marathon", "ultra"):
        parts.append("For long distance, maintaining your baseline mechanics under fatigue will yield the largest energy savings.")

    return " ".join(parts)


def _val(metrics: Dict, key: str) -> Optional[float]:
    m = metrics.get(key)
    return m.get("value") if isinstance(m, dict) else None


def _baseline_dev(baseline: Dict, baseline_key: str, metrics: Dict, metrics_key: str) -> Optional[float]:
    bval = baseline.get(baseline_key)
    mval = _val(metrics, metrics_key)
    if bval and mval and bval != 0:
        return round(((mval - bval) / abs(bval)) * 100, 1)
    return None


def _fmt_time(s: Optional[float]) -> str:
    if s is None:
        return "unknown"
    m = int(s // 60)
    sec = s % 60
    return f"{m:02d}:{sec:05.2f}"
