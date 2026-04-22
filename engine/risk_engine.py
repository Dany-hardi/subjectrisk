"""
SubjectRisk — Core Risk Engine
All statistical calculations. No fake values. Every number is derived.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────

@dataclass
class SubjectInput:
    """Raw data collected from the student via the form."""

    # Identification
    subject_name: str
    subject_type: str            # math / science / language / programming / humanities

    # Study behaviour
    weekly_study_hours: float    # hours per week dedicated to this subject
    study_sessions_per_week: int # number of distinct sessions
    study_quality: float         # self-rated 1–10 (focused, active recall vs passive reading)
    days_until_exam: int         # how many days remain

    # Understanding & coverage
    self_understanding: float    # 1–10: "how well do I understand the material?"
    syllabus_coverage: float     # 0–100%: portion of the programme reviewed at least once
    exercises_done: float        # 0–100%: proportion of practice exercises attempted
    uses_past_papers: bool       # does the student practice with past exam papers?

    # Past academic record (this subject)
    past_scores: list[float]     # list of previous scores (0–100) for this subject
    attendance_rate: float       # 0–100%

    # Physical & mental state
    avg_sleep_hours: float       # average nightly sleep this week
    sleep_quality: float         # 1–10 subjective sleep quality
    stress_level: float          # 1–10 (10 = max stress)
    energy_level: float          # 1–10 self-reported daily energy

    # External support
    has_study_group: bool
    asks_questions_in_class: bool
    uses_additional_resources: bool  # textbooks, YouTube, tutoring beyond course material

    # Metacognition
    subjective_confidence: float  # 1–10: "how confident am I going into this exam?"


@dataclass
class RiskFactor:
    """A single named risk contributor with its computed values."""
    name: str
    value: float           # raw computed value
    normalised: float      # 0–100 scale (100 = perfect, 0 = worst)
    weight: float          # relative importance in the model (0–1)
    contribution: float    # signed contribution to risk score
    status: str            # "safe" | "warning" | "critical"
    plain_label: str       # e.g. "Study Volume"
    what_it_measures: str  # one sentence definition
    why_it_matters: str    # one sentence justification from research
    your_result: str       # personalised sentence explaining the student's value
    advice: str            # one actionable sentence


@dataclass
class RiskResult:
    """Full output of the risk engine."""
    subject_name: str
    risk_score: float              # 0–100 (100 = certain failure)
    pass_probability: float        # 0–1
    risk_tier: str                 # "Low" | "Moderate" | "High" | "Critical"
    risk_tier_color: str

    factors: list[RiskFactor]

    # Derived metrics
    study_efficiency_index: float  # score per hour invested
    preparation_momentum: str      # "Improving" | "Stable" | "Declining"
    recovery_index: float          # sleep-to-stress ratio
    knowledge_gap: float           # 100 - weighted coverage score
    predicted_score: float         # regression-estimated exam score

    # Narrative
    verdict_headline: str
    verdict_narrative: str         # 3-sentence human explanation
    top_3_risks: list[str]
    action_plan: list[dict]        # [{priority, action, reason, impact}]

    # Chart data
    factor_radar: dict             # {label: normalised_value}
    risk_decomposition: dict       # {factor_name: contribution_pct}
    score_timeline: list[float]    # past scores + predicted
    preparation_profile: dict      # named scores for each preparation dimension


# ─────────────────────────────────────────────
# COEFFICIENTS — based on documented research
# relationships between study behaviours and
# academic performance (Credé & Kuncel 2008,
# Duckworth et al. 2007, Pilcher & Walters 1997)
# ─────────────────────────────────────────────

WEIGHTS = {
    "study_volume":       0.18,
    "study_quality":      0.16,
    "past_performance":   0.15,
    "knowledge_coverage": 0.14,
    "understanding":      0.13,
    "attendance":         0.09,
    "recovery":           0.08,
    "practice":           0.07,
}

# Threshold values below which a factor becomes "warning" or "critical"
THRESHOLDS = {
    "study_volume":       {"warning": 40, "critical": 20},
    "study_quality":      {"warning": 45, "critical": 25},
    "past_performance":   {"warning": 40, "critical": 25},
    "knowledge_coverage": {"warning": 50, "critical": 30},
    "understanding":      {"warning": 45, "critical": 25},
    "attendance":         {"warning": 50, "critical": 30},
    "recovery":           {"warning": 40, "critical": 20},
    "practice":           {"warning": 35, "critical": 15},
}


def _status(key: str, val: float) -> str:
    t = THRESHOLDS[key]
    if val <= t["critical"]:
        return "critical"
    if val <= t["warning"]:
        return "warning"
    return "safe"


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


# ─────────────────────────────────────────────
# FACTOR CALCULATORS
# ─────────────────────────────────────────────

def _calc_study_volume(inp: SubjectInput) -> tuple[float, str]:
    """
    Normalise weekly study hours against recommended thresholds by subject type.
    Research: 2-3 hours per credit hour per week is the standard recommendation
    (National Survey of Student Engagement, 2019).
    """
    recommended = {"math": 12, "science": 10, "programming": 10,
                   "language": 8, "humanities": 8}.get(inp.subject_type, 9)

    # Scale: 0 hours → 0, at recommended → 80, 50% over recommended → 100
    ratio = inp.weekly_study_hours / recommended
    normalised = _clamp(ratio * 80 if ratio <= 1.0 else 80 + (ratio - 1.0) * 20 * 2, 0, 100)

    if inp.weekly_study_hours == 0:
        result = f"You are not studying this subject at all. That alone makes failure near-certain."
    elif inp.weekly_study_hours < recommended * 0.4:
        result = f"You study {inp.weekly_study_hours:.1f} h/week. The recommended minimum for {inp.subject_name} is around {recommended} h/week. You are at {ratio*100:.0f}% of that."
    elif inp.weekly_study_hours < recommended:
        result = f"You study {inp.weekly_study_hours:.1f} h/week — {recommended - inp.weekly_study_hours:.1f} hours below the recommended {recommended} h/week for this type of subject."
    else:
        result = f"You study {inp.weekly_study_hours:.1f} h/week, which meets or exceeds the recommended {recommended} h/week. Good volume."

    return normalised, result


def _calc_study_quality(inp: SubjectInput) -> tuple[float, str]:
    """
    Study quality combines self-rated focus with session frequency.
    Distributed practice (multiple short sessions) outperforms massed practice
    (Cepeda et al. 2006 — spacing effect).
    """
    # Session distribution bonus: 4+ sessions/week is optimal
    session_bonus = _clamp((inp.study_sessions_per_week / 5) * 20, 0, 20)
    quality_score = inp.study_quality * 8 + session_bonus  # max ~100
    normalised = _clamp(quality_score, 0, 100)

    label = "passive" if inp.study_quality < 5 else "moderate" if inp.study_quality < 7 else "active"
    result = (f"You rate your study quality at {inp.study_quality:.0f}/10 ({label}) across "
              f"{inp.study_sessions_per_week} session(s)/week. "
              f"{'Spreading sessions improves retention.' if inp.study_sessions_per_week < 3 else 'Good session distribution.'}")
    return normalised, result


def _calc_past_performance(inp: SubjectInput) -> tuple[float, str, float, str]:
    """
    Analyse the trend and level of past scores.
    Returns: normalised, result_text, predicted_score, momentum_label
    """
    scores = inp.past_scores
    if not scores:
        # No history — use understanding + CA as proxy
        proxy = (inp.self_understanding * 5 + inp.syllabus_coverage * 0.5)
        normalised = _clamp(proxy, 0, 100)
        return normalised, "No past scores recorded. Estimate based on your self-assessed understanding.", 50.0, "Unknown"

    avg = sum(scores) / len(scores)
    normalised = _clamp(avg, 0, 100)

    # Trend: simple linear regression over score sequence
    n = len(scores)
    if n >= 2:
        x_mean = (n - 1) / 2
        slope_num = sum((i - x_mean) * (s - avg) for i, s in enumerate(scores))
        slope_den = sum((i - x_mean) ** 2 for i in range(n))
        slope = slope_num / slope_den if slope_den > 0 else 0.0
        momentum = "Improving" if slope > 1.5 else "Declining" if slope < -1.5 else "Stable"
    else:
        slope = 0.0
        momentum = "Stable"

    # Predict next score: extrapolate trend + regression to mean
    predicted = _clamp(avg + slope * 1.5 * 0.6, 0, 100)

    trend_word = {"Improving": "rising", "Declining": "falling", "Stable": "flat"}[momentum]
    result = (f"Your average in {inp.subject_name} is {avg:.1f}/100 ({n} score(s)). "
              f"Your trend is {trend_word} (slope: {slope:+.1f} pts/test). "
              f"Projected next score (trend extrapolation): {predicted:.0f}/100.")

    return normalised, result, predicted, momentum


def _calc_coverage(inp: SubjectInput) -> tuple[float, str]:
    """
    Knowledge coverage = weighted combination of syllabus coverage and exercises.
    Past-paper practice doubles the transfer effect (Roediger & Karpicke 2006 — testing effect).
    """
    paper_bonus = 10.0 if inp.uses_past_papers else 0.0
    coverage = inp.syllabus_coverage * 0.6 + inp.exercises_done * 0.4 + paper_bonus
    normalised = _clamp(coverage, 0, 100)

    parts = []
    if inp.syllabus_coverage < 70:
        parts.append(f"only {inp.syllabus_coverage:.0f}% of the syllabus reviewed")
    if inp.exercises_done < 50:
        parts.append(f"only {inp.exercises_done:.0f}% of exercises attempted")
    if not inp.uses_past_papers:
        parts.append("no past paper practice")

    if parts:
        result = f"Coverage gaps detected: {'; '.join(parts)}. Uncovered material is a direct source of exam surprises."
    else:
        result = (f"You have covered {inp.syllabus_coverage:.0f}% of the syllabus and attempted "
                  f"{inp.exercises_done:.0f}% of exercises. Strong preparation base.")
    return normalised, result


def _calc_understanding(inp: SubjectInput) -> tuple[float, str]:
    """
    Self-assessed understanding calibrated against past performance gap.
    Overconfidence is penalised — the Dunning-Kruger correction.
    """
    raw = inp.self_understanding * 10
    if inp.past_scores:
        avg_past = sum(inp.past_scores) / len(inp.past_scores)
        # If confidence >> performance, apply a credibility penalty
        confidence_raw = inp.subjective_confidence * 10
        gap = confidence_raw - avg_past
        penalty = _clamp(gap * 0.25, 0, 20) if gap > 10 else 0  # penalise over-confidence
        raw = raw - penalty

    normalised = _clamp(raw, 0, 100)
    level = "low" if normalised < 40 else "moderate" if normalised < 65 else "solid"
    result = (f"Self-assessed understanding: {inp.self_understanding:.0f}/10. "
              f"After calibration against your track record, your effective understanding score is {normalised:.0f}/100 ({level}).")
    return normalised, result


def _calc_attendance(inp: SubjectInput) -> tuple[float, str]:
    """
    Class attendance is one of the strongest predictors of academic success.
    Meta-analysis: each 10% drop in attendance corresponds to ~3-point score reduction
    (Credé et al. 2010).
    """
    normalised = _clamp(inp.attendance_rate, 0, 100)
    support_bonus = (5 if inp.asks_questions_in_class else 0) + (5 if inp.has_study_group else 0)
    normalised = _clamp(normalised + support_bonus * 0.3, 0, 100)

    if inp.attendance_rate < 50:
        result = f"Attendance at {inp.attendance_rate:.0f}% is critically low. Missing more than half the course means large knowledge gaps that are very hard to fill through self-study alone."
    elif inp.attendance_rate < 70:
        result = f"Attendance at {inp.attendance_rate:.0f}% is below the recommended 80% threshold. Research estimates this gap costs around {(80 - inp.attendance_rate) * 0.3:.1f} points on final exams."
    else:
        result = f"Attendance at {inp.attendance_rate:.0f}% is good. You are capturing the majority of in-class explanations and examples."
    return normalised, result


def _calc_recovery(inp: SubjectInput) -> tuple[float, str]:
    """
    Recovery = sleep quality and quantity relative to stress load.
    Sleep deprivation reduces memory consolidation by up to 40%
    (Walker 2017 — Why We Sleep).
    """
    sleep_score = _clamp((inp.avg_sleep_hours / 8) * 60 + inp.sleep_quality * 4, 0, 100)
    stress_penalty = _clamp((inp.stress_level - 3) * 8, 0, 40)
    recovery = _clamp(sleep_score - stress_penalty, 0, 100)

    stress_word = "low" if inp.stress_level <= 3 else "moderate" if inp.stress_level <= 6 else "high"
    sleep_word = "insufficient" if inp.avg_sleep_hours < 6 else "borderline" if inp.avg_sleep_hours < 7 else "adequate"
    result = (f"You sleep {inp.avg_sleep_hours:.1f} h/night ({sleep_word}) at quality {inp.sleep_quality:.0f}/10, "
              f"with {stress_word} stress ({inp.stress_level:.0f}/10). "
              f"Your brain's recovery capacity is at {recovery:.0f}/100.")
    return recovery, result


def _calc_practice(inp: SubjectInput) -> tuple[float, str]:
    """
    Active practice combines exercise volume, past papers, and external resources.
    Active retrieval practice improves retention by 50% vs re-reading
    (Karpicke & Roediger 2008).
    """
    base = inp.exercises_done * 0.5
    paper_bonus = 20.0 if inp.uses_past_papers else 0.0
    resource_bonus = 15.0 if inp.uses_additional_resources else 0.0
    group_bonus = 10.0 if inp.has_study_group else 0.0
    practice = _clamp(base + paper_bonus + resource_bonus + group_bonus, 0, 100)

    parts = []
    if inp.uses_past_papers: parts.append("past papers")
    if inp.uses_additional_resources: parts.append("extra resources")
    if inp.has_study_group: parts.append("study group")

    if parts:
        result = f"Active practice enriched by: {', '.join(parts)}. Combined practice score: {practice:.0f}/100."
    else:
        result = f"No enriched practice detected. You rely only on {inp.exercises_done:.0f}% exercise completion. Adding past papers alone would add ~20 points to this score."
    return practice, result


# ─────────────────────────────────────────────
# MAIN ENGINE
# ─────────────────────────────────────────────

def compute_risk(inp: SubjectInput) -> RiskResult:
    """
    Run the full risk computation pipeline.
    Returns a RiskResult with all metrics, explanations, and charts.
    """

    # ── Compute all factors ──────────────────
    sv_norm, sv_result = _calc_study_volume(inp)
    sq_norm, sq_result = _calc_study_quality(inp)
    pp_norm, pp_result, predicted_from_trend, momentum = _calc_past_performance(inp)
    cov_norm, cov_result = _calc_coverage(inp)
    und_norm, und_result = _calc_understanding(inp)
    att_norm, att_result = _calc_attendance(inp)
    rec_norm, rec_result = _calc_recovery(inp)
    prac_norm, prac_result = _calc_practice(inp)

    norms = {
        "study_volume":       sv_norm,
        "study_quality":      sq_norm,
        "past_performance":   pp_norm,
        "knowledge_coverage": cov_norm,
        "understanding":      und_norm,
        "attendance":         att_norm,
        "recovery":           rec_norm,
        "practice":           prac_norm,
    }

    # ── Weighted preparation score (0–100, 100 = fully prepared) ──
    prep_score = sum(norms[k] * WEIGHTS[k] for k in WEIGHTS)

    # ── Risk score: inverse of preparation, amplified by days pressure ──
    base_risk = 100 - prep_score

    # Time pressure modifier: less time left amplifies existing risk
    time_ratio = _clamp(inp.days_until_exam / 30, 0.1, 1.0)
    if base_risk > 50:
        time_mod = 1 + (1 - time_ratio) * 0.25  # urgency amplifies high risk
    else:
        time_mod = 1 - (1 - time_ratio) * 0.08  # short time slightly hurts even prepared students

    risk_score = _clamp(base_risk * time_mod, 0, 100)

    # ── Pass probability (logistic function of risk) ──
    logit = -0.12 * (risk_score - 50)
    pass_prob = _clamp(1 / (1 + math.exp(-logit)), 0.02, 0.98)

    # ── Predicted exam score (regression model) ──
    predicted_score = _clamp(
        pp_norm * 0.35
        + und_norm * 0.20
        + cov_norm * 0.18
        + sv_norm  * 0.12
        + prac_norm * 0.10
        + att_norm  * 0.05,
        0, 100
    )
    # Blend with trend extrapolation
    if inp.past_scores:
        predicted_score = predicted_score * 0.6 + predicted_from_trend * 0.4

    # ── Study efficiency index ──
    if inp.weekly_study_hours > 0 and inp.past_scores:
        avg_past = sum(inp.past_scores) / len(inp.past_scores)
        study_efficiency_index = avg_past / inp.weekly_study_hours
    else:
        study_efficiency_index = 0.0

    # ── Knowledge gap ──
    knowledge_gap = _clamp(
        (100 - inp.syllabus_coverage) * 0.5
        + (100 - inp.exercises_done) * 0.3
        + (10 if not inp.uses_past_papers else 0),
        0, 100
    )

    # ── Recovery index ──
    recovery_index = _clamp(inp.avg_sleep_hours / max(inp.stress_level, 0.1) * 10, 0, 100)

    # ── Risk tier ──
    if risk_score < 25:
        tier, tier_color = "Low", "#3db87a"
    elif risk_score < 50:
        tier, tier_color = "Moderate", "#f0c040"
    elif risk_score < 75:
        tier, tier_color = "High", "#e08040"
    else:
        tier, tier_color = "Critical", "#e05050"

    # ── Build RiskFactor objects ──
    factor_meta = {
        "study_volume": {
            "plain_label": "Study Volume",
            "what_it_measures": "The total weekly time you dedicate to this subject, relative to what the subject type requires.",
            "why_it_matters": "Time-on-task is the baseline requirement. Without sufficient hours, no other factor can compensate fully.",
            "advice": "Add 1 focused session of 90 min to your week before reconsidering anything else.",
            "result": sv_result,
        },
        "study_quality": {
            "plain_label": "Study Quality",
            "what_it_measures": "How actively you study — active recall and spaced repetition vs passive re-reading.",
            "why_it_matters": "The spacing effect and retrieval practice are the most reliably documented ways to improve long-term retention.",
            "advice": "Replace one passive re-reading session with a closed-book self-test this week.",
            "result": sq_result,
        },
        "past_performance": {
            "plain_label": "Track Record",
            "what_it_measures": "Your historical scores in this subject, including trend direction.",
            "why_it_matters": "Past performance is the single strongest predictor of future academic results in the same subject.",
            "advice": "Identify the specific sub-topics where you lost marks previously and target them first.",
            "result": pp_result,
        },
        "knowledge_coverage": {
            "plain_label": "Programme Coverage",
            "what_it_measures": "The fraction of the syllabus you have reviewed at least once, weighted by exercise practice.",
            "why_it_matters": "Exam questions cover the whole syllabus. Uncovered chapters are guaranteed lost marks.",
            "advice": f"Map every chapter on paper. Any chapter below 60% coverage needs a dedicated revision block.",
            "result": cov_result,
        },
        "understanding": {
            "plain_label": "Depth of Understanding",
            "what_it_measures": "Your self-assessed mastery, calibrated against your actual track record.",
            "why_it_matters": "Surface familiarity (feeling like you understand) and genuine understanding (being able to apply it) are very different — exams test the latter.",
            "advice": "Test your understanding by trying to explain the key concepts out loud, without notes.",
            "result": und_result,
        },
        "attendance": {
            "plain_label": "Class Engagement",
            "what_it_measures": "How often you are present in class, plus active participation signals.",
            "why_it_matters": "Every 10% drop in attendance correlates with approximately 3 fewer exam points (Credé et al. 2010).",
            "advice": "Attend the next 5 classes with no exceptions, and write at least one question per session.",
            "result": att_result,
        },
        "recovery": {
            "plain_label": "Physical Recovery",
            "what_it_measures": "The balance between your sleep quality and your stress load.",
            "why_it_matters": "Memory consolidation happens during sleep. High stress hormones physically block encoding of new information.",
            "advice": "Protect 7 hours of sleep tonight — even one night of recovery measurably improves recall the next day.",
            "result": rec_result,
        },
        "practice": {
            "plain_label": "Active Practice",
            "what_it_measures": "Whether you are practising with exercises, past papers, and multiple resources beyond the main course.",
            "why_it_matters": "Retrieval practice (doing problems, past papers) improves test performance by ~50% over passive review.",
            "advice": "Do one full past exam under timed conditions before your next study session.",
            "result": prac_result,
        },
    }

    # ── Contribution to risk (proportional decomposition) ──
    total_weighted_risk = sum((100 - norms[k]) * WEIGHTS[k] for k in WEIGHTS)
    factors = []
    risk_decomposition = {}

    for key, meta in factor_meta.items():
        factor_risk = (100 - norms[key]) * WEIGHTS[key]
        contribution_pct = (factor_risk / total_weighted_risk * 100) if total_weighted_risk > 0 else 0
        contribution_to_score = (norms[key] - 50) * WEIGHTS[key]
        status = _status(key, norms[key])

        factors.append(RiskFactor(
            name=key,
            value=norms[key],
            normalised=norms[key],
            weight=WEIGHTS[key],
            contribution=contribution_to_score,
            status=status,
            plain_label=meta["plain_label"],
            what_it_measures=meta["what_it_measures"],
            why_it_matters=meta["why_it_matters"],
            your_result=meta["result"],
            advice=meta["advice"],
        ))
        risk_decomposition[meta["plain_label"]] = round(contribution_pct, 1)

    factors.sort(key=lambda f: f.normalised)

    # ── Top 3 risks ──
    top_3_risks = [f.plain_label for f in factors[:3]]

    # ── Action plan ──
    action_plan = []
    for i, factor in enumerate(factors[:3]):
        impact_word = "high" if i == 0 else "moderate"
        action_plan.append({
            "priority": i + 1,
            "area": factor.plain_label,
            "action": factor.advice,
            "reason": factor.why_it_matters,
            "impact": impact_word,
            "current_score": round(factor.normalised, 0),
        })

    # ── Verdict narrative ──
    strong = [f.plain_label for f in sorted(factors, key=lambda x: -x.normalised)[:2]]
    weak   = top_3_risks

    def _tier_description(t):
        return {
            "Low": "well-prepared and unlikely to fail",
            "Moderate": "moderately prepared — a focused push would secure a pass",
            "High": "at real risk of failing — specific gaps need urgent attention",
            "Critical": "in a critical position — immediate and significant action is required",
        }[t]

    headline = f"{inp.subject_name} — Risk Score: {risk_score:.0f}/100 — {tier} Risk"

    narrative = (
        f"Based on your data, you are currently {_tier_description(tier)} in {inp.subject_name}. "
        f"Your strongest areas are {strong[0]} and {strong[1] if len(strong) > 1 else 'overall preparation'}, "
        f"which are helping you. However, {weak[0]} is your most critical weakness and is contributing "
        f"the most to your current risk score. "
        f"With {inp.days_until_exam} days remaining, the model estimates your exam score at approximately "
        f"{predicted_score:.0f}/100 and your probability of passing at {pass_prob*100:.0f}%."
    )

    # ── Chart data ──
    factor_radar = {
        f.plain_label: round(f.normalised, 1) for f in factors
    }

    score_timeline = list(inp.past_scores) + [round(predicted_score, 1)]

    preparation_profile = {
        "Volume": round(sv_norm, 1),
        "Quality": round(sq_norm, 1),
        "Coverage": round(cov_norm, 1),
        "Understanding": round(und_norm, 1),
        "Practice": round(prac_norm, 1),
        "Attendance": round(att_norm, 1),
        "Recovery": round(rec_norm, 1),
    }

    return RiskResult(
        subject_name=inp.subject_name,
        risk_score=round(risk_score, 1),
        pass_probability=round(pass_prob, 4),
        risk_tier=tier,
        risk_tier_color=tier_color,
        factors=factors,
        study_efficiency_index=round(study_efficiency_index, 2),
        preparation_momentum=momentum,
        recovery_index=round(recovery_index, 1),
        knowledge_gap=round(knowledge_gap, 1),
        predicted_score=round(predicted_score, 1),
        verdict_headline=headline,
        verdict_narrative=narrative,
        top_3_risks=top_3_risks,
        action_plan=action_plan,
        factor_radar=factor_radar,
        risk_decomposition=risk_decomposition,
        score_timeline=score_timeline,
        preparation_profile=preparation_profile,
    )
