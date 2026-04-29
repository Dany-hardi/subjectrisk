"""
SubjectRisk — Main Streamlit Application
Bloomberg Terminal theme · Black & Gold
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.risk_engine import SubjectInput, compute_risk, RiskResult, RiskFactor
from engine.charts import (
    risk_gauge, factor_radar, risk_decomposition_chart,
    score_timeline_chart, preparation_bars, pass_probability_bar,
)

# ── Color constants (Bloomberg Terminal palette) ──────────────
GOLD     = "#f0c040"
GOLD_DIM = "#c89a28"
GREEN    = "#3db87a"
RED      = "#e05050"
ORANGE   = "#e08040"
BLUE     = "#4a9ee8"
DIM      = "#666666"
TEXT     = "#eeeeee"
TEXT2    = "#aaaaaa"
SURFACE  = "#111111"
CARD     = "#181818"
BORDER   = "#2a2a2a"


# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SubjectRisk — Exam Risk Analyser",
    page_icon="▸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject CSS
with open(os.path.join(os.path.dirname(__file__), "assets/style.css")) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

STATUS_ICONS = {"safe": "●", "warning": "◐", "critical": "○"}
STATUS_COLORS_CSS = {"safe": "#3db87a", "warning": "#f0c040", "critical": "#e05050"}

TIER_COLORS = {
    "Low":      "#3db87a",
    "Moderate": "#f0c040",
    "High":     "#e08040",
    "Critical": "#e05050",
}

def colored(text: str, color: str) -> str:
    return f'<span style="color:{color};font-weight:700">{text}</span>'

def card(content: str, border_color: str = "#2a2a2a") -> None:
    st.markdown(
        f'<div style="background:#181818;border:1px solid {border_color};'
        f'border-radius:3px;padding:16px 18px;margin-bottom:10px">{content}</div>',
        unsafe_allow_html=True,
    )

def section_header(title: str, subtitle: str = "") -> None:
    sub = f'<div style="color:#666;font-size:11px;letter-spacing:.08em;margin-top:3px">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div style="border-left:3px solid #f0c040;padding-left:12px;margin:28px 0 14px">'
        f'<div style="color:#f0c040;font-size:12px;letter-spacing:.12em;text-transform:uppercase;font-weight:700">'
        f'{title}</div>{sub}</div>',
        unsafe_allow_html=True,
    )

def factor_badge(status: str, label: str) -> str:
    color = STATUS_COLORS_CSS[status]
    icon = STATUS_ICONS[status]
    return (f'<span style="color:{color};font-size:10px;font-weight:700;'
            f'border:1px solid {color};padding:1px 7px;border-radius:2px;'
            f'letter-spacing:.06em">{icon} {label.upper()}</span>')


# ─────────────────────────────────────────────────────────────
# TOP BAR
# ─────────────────────────────────────────────────────────────

st.markdown("""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:10px 0 20px;border-bottom:1px solid #1e1e1e;margin-bottom:24px">
  <div>
    <span style="color:#f0c040;font-size:20px;font-weight:700;letter-spacing:.1em">SUBJECTRISK</span>
    <span style="color:#444;font-size:11px;margin-left:14px">/ EXAM FAILURE PREDICTION ENGINE</span>
  </div>
  <div style="color:#444;font-size:10px;letter-spacing:.08em">
    REGRESSION · LOGISTIC · WEIGHTED COMPOSITE · v1.0
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────

if "result" not in st.session_state:
    st.session_state.result = None
if "show_results" not in st.session_state:
    st.session_state.show_results = False
if "page" not in st.session_state:
    st.session_state.page = "landing"   # "landing" | "form" | "results" 



# ─────────────────────────────────────────────────────────────
# LANDING PAGE
# ─────────────────────────────────────────────────────────────

def render_landing():
    # ── Hero block ────────────────────────────────────────────
    st.markdown("""
<div style="text-align:center;padding:40px 0 32px">
  <div style="color:#f0c040;font-size:11px;letter-spacing:.2em;text-transform:uppercase;margin-bottom:14px">
    Exam Preparation Intelligence
  </div>
  <div style="color:#eeeeee;font-size:32px;font-weight:700;letter-spacing:.04em;line-height:1.3;margin-bottom:18px">
    Do you know your real risk<br>of failing your next exam?
    <br>Answer this form and get to know<br>whether you're ready or not.!
  </div>
  <div style="color:#888;font-size:14px;max-width:560px;margin:0 auto;line-height:1.9">
    Most students feel either falsely confident or needlessly anxious before an exam —
    because they have no objective measure of where they actually stand.
    <strong style="color:#cccccc">SubjectRisk</strong> changes that.
  </div>
</div>
""", unsafe_allow_html=True)

    # ── What it does ──────────────────────────────────────────
    section_header("WHAT THIS APP DOES", "One subject. One exam. One honest answer.")

    st.markdown("""
<div style="color:#aaaaaa;font-size:13px;line-height:1.9;margin-bottom:20px">
You enter data about <strong style="color:#eeeeee">one specific subject</strong> you are preparing for —
your study habits, your past scores, how much of the programme you have covered,
your sleep and stress levels, and more.
<br><br>
The app runs those numbers through a <strong style="color:#eeeeee">weighted statistical model</strong>
built on peer-reviewed research in educational psychology. It then produces a
<strong style="color:#f0c040">risk score from 0 to 100</strong>, a pass probability, a predicted exam score,
and a breakdown of exactly which factors are hurting you the most — each one explained
in plain language, not statistical jargon.
<br><br>
The goal is simple: <strong style="color:#eeeeee">give you a clear, honest, justified picture of where you stand</strong>
so you can make better decisions about where to focus your remaining preparation time.
</div>
""", unsafe_allow_html=True)

    # ── 3 columns: what you get ───────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
<div style="background:#181818;border:1px solid #2a2a2a;border-top:2px solid #f0c040;
            border-radius:3px;padding:18px 16px;height:100%">
  <div style="color:#f0c040;font-size:11px;letter-spacing:.12em;text-transform:uppercase;margin-bottom:10px">
    Risk Score
  </div>
  <div style="color:#eeeeee;font-size:13px;line-height:1.8">
    A single number — 0 to 100 — that summarises your current probability of failing,
    calculated from 8 independent factors with documented weights.
  </div>
</div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("""
<div style="background:#181818;border:1px solid #2a2a2a;border-top:2px solid #f0c040;
            border-radius:3px;padding:18px 16px;height:100%">
  <div style="color:#f0c040;font-size:11px;letter-spacing:.12em;text-transform:uppercase;margin-bottom:10px">
    Factor Breakdown
  </div>
  <div style="color:#eeeeee;font-size:13px;line-height:1.8">
    Every dimension — study volume, coverage, sleep, past scores, attendance — is
    scored individually and explained with its specific contribution to your risk.
  </div>
</div>""", unsafe_allow_html=True)

    with c3:
        st.markdown("""
<div style="background:#181818;border:1px solid #2a2a2a;border-top:2px solid #f0c040;
            border-radius:3px;padding:18px 16px;height:100%">
  <div style="color:#f0c040;font-size:11px;letter-spacing:.12em;text-transform:uppercase;margin-bottom:10px">
    Action Plan
  </div>
  <div style="color:#eeeeee;font-size:13px;line-height:1.8">
    Three prioritised actions derived directly from your weakest factors —
    not generic advice, but specific steps calculated from your own data.
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── How it works ──────────────────────────────────────────
    section_header("HOW IT WORKS", "No fake data. No generic scores. Everything computed from what you enter.")

    st.markdown("""
<div style="color:#aaaaaa;font-size:13px;line-height:1.9;margin-bottom:6px">
<strong style="color:#eeeeee">Step 1 — You fill in the form.</strong>
About 20 questions covering your study behaviour, academic record, physical state,
and use of resources — all specific to the subject and exam you are targeting.
It takes roughly 3 minutes.
<br><br>
<strong style="color:#eeeeee">Step 2 — The model computes 8 risk factors.</strong>
Each factor is calculated using a documented formula (not an opinion), normalised to a
0–100 scale, and weighted by its empirically established importance. The weights come
from meta-analyses in educational psychology — Credé & Kuncel (2008), Karpicke & Roediger (2008),
Walker (2017), and others.
<br><br>
<strong style="color:#eeeeee">Step 3 — You get a full report.</strong>
A risk gauge, a pass probability, a predicted score, charts, and a factor-by-factor
explanation — all generated from your data, recalculated every time you submit.
</div>
""", unsafe_allow_html=True)

    # ── Important note ────────────────────────────────────────
    st.markdown("""
<div style="background:#0f1a10;border:1px solid #1a3020;border-left:3px solid #3db87a;
            border-radius:0 3px 3px 0;padding:12px 16px;margin:10px 0 28px">
  <span style="color:#3db87a;font-size:10px;letter-spacing:.1em;text-transform:uppercase;
               font-weight:700">Important</span><br>
  <span style="color:#aaaaaa;font-size:12px;line-height:1.8">
    This tool produces <strong style="color:#cccccc">statistical estimates</strong>, not guarantees.
    Its accuracy depends entirely on the honesty and accuracy of what you enter.
    A student who inflates their scores or underestimates their stress will get a misleadingly
    optimistic result. Enter your real data to get a useful result.
  </span>
</div>
""", unsafe_allow_html=True)

    # ── CTA button ────────────────────────────────────────────
    col_l, col_c, col_r = st.columns([1.5, 1, 1.5])
    with col_c:
        if st.button("▶  START MY ANALYSIS", use_container_width=True):
            st.session_state.page = "form"
            st.rerun()

    # ── Footer note ───────────────────────────────────────────
    st.markdown("""
<div style="text-align:center;margin-top:40px;color:#333;font-size:10px">
  SubjectRisk · Built with Python, Streamlit, and Plotly ·
  Model based on peer-reviewed research in educational psychology
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# FORM
# ─────────────────────────────────────────────────────────────

def render_form():
    # Back to landing
    if st.button("← BACK"):
        st.session_state.page = "landing"
        st.rerun()

    st.markdown(
        '<p style="color:#666;font-size:12px;margin-bottom:24px">'
        'Answer every question as honestly as possible. The more accurate your inputs, '
        'the more reliable your risk prediction. This form takes about 3 minutes.</p>',
        unsafe_allow_html=True,
    )

    with st.form("risk_form", clear_on_submit=False):

        # ── BLOCK 1: Subject ─────────────────────────────────
        section_header("01 · The Subject", "Tell us what exam you are preparing for")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            subject_name = st.text_input(
                "Subject name",
                value="",
                placeholder="e.g. Linear Algebra, Algorithms, Organic Chemistry…",
                help="Enter the exact subject name — this contextualises the recommendations.",
            )
        with col2:
            subject_type = st.selectbox(
                "Subject category",
                options=["math", "science", "programming", "language", "humanities"],
                format_func=lambda x: {
                    "math": "Mathematics",
                    "science": "Science / Physics",
                    "programming": "Programming / CS",
                    "language": "Language / Literature",
                    "humanities": "Humanities / Social Sci.",
                }[x],
            )
        with col3:
            days_until_exam = st.number_input(
                "Days until the exam",
                min_value=1, max_value=365, value=21, step=1,
                help="How many days remain before the exam? This affects the urgency of your risk score.",
            )

        # ── BLOCK 2: Study Behaviour ─────────────────────────
        section_header("02 · Your Study Behaviour", "For this specific subject — not all your studying combined")

        col1, col2 = st.columns(2)
        with col1:
            weekly_study_hours = st.slider(
                "Hours you study this subject per week",
                min_value=0.0, max_value=30.0, value=5.0, step=0.5,
                help="Count only focused study time for this subject. Not time sitting at a desk.",
            )
            st.caption(f"→ {weekly_study_hours:.1f} h/week · {weekly_study_hours/7:.1f} h/day on average")

            study_sessions_per_week = st.slider(
                "How many distinct study sessions per week?",
                min_value=1, max_value=14, value=3, step=1,
                help="Spreading study across multiple short sessions (spaced practice) is more effective than one long block.",
            )
            st.caption("Research: 4+ sessions/week maximises retention (spacing effect)")

        with col2:
            study_quality = st.slider(
                "How focused and active is your study? (1 = I re-read notes; 10 = I actively test myself)",
                min_value=1.0, max_value=10.0, value=5.0, step=0.5,
                help="Active recall (doing problems, self-testing) is ~50% more effective than passive review.",
            )
            quality_label = "Passive (re-reading)" if study_quality < 4 else \
                            "Mixed" if study_quality < 7 else "Active (retrieval practice)"
            st.caption(f"→ {quality_label}")

            uses_past_papers = st.checkbox(
                "I regularly practise with past exam papers",
                help="Past paper practice is the single highest-impact preparation activity.",
            )

        # ── BLOCK 3: Programme Coverage ──────────────────────
        section_header("03 · Programme Coverage", "How much of the syllabus have you actually worked through?")

        col1, col2 = st.columns(2)
        with col1:
            syllabus_coverage = st.slider(
                "% of the syllabus you have reviewed at least once",
                min_value=0, max_value=100, value=60, step=5,
                help="Be honest. If you have only glanced at a chapter, do not count it as covered.",
            )
            gap_label = "CRITICAL GAP" if syllabus_coverage < 40 else \
                        "Significant gap" if syllabus_coverage < 65 else \
                        "Good coverage" if syllabus_coverage < 85 else "Excellent"
            st.caption(f"→ {gap_label} — {100 - syllabus_coverage}% still unreviewed")

        with col2:
            exercises_done = st.slider(
                "% of available practice exercises you have attempted",
                min_value=0, max_value=100, value=40, step=5,
                help="Exercises include problem sets, homework, practice questions, and any active practice.",
            )
            st.caption(f"→ {exercises_done}% attempted · {100 - exercises_done}% remaining")

        # ── BLOCK 4: Past Academic Record ────────────────────
        section_header("04 · Your Past Results In This Subject", "Enter your actual scores — these are the most powerful predictors")

        st.markdown(
            '<p style="color:#555;font-size:11px;margin-bottom:12px">'
            'Enter up to 5 past scores (0–100) for this subject. '
            'Tests, midterms, homework averages — anything graded. '
            'Leave blank if this is your first time taking this subject.</p>',
            unsafe_allow_html=True,
        )

        pcols = st.columns(5)
        raw_scores = []
        placeholders = ["1st test", "2nd test", "3rd test", "4th test", "5th test"]
        for i, col in enumerate(pcols):
            with col:
                val = st.number_input(
                    placeholders[i], min_value=0.0, max_value=100.0,
                    value=None, step=0.5, format="%.1f",
                    key=f"score_{i}",
                    label_visibility="visible",
                )
                if val is not None:
                    raw_scores.append(float(val))

        if raw_scores:
            avg = sum(raw_scores) / len(raw_scores)
            trend = ""
            if len(raw_scores) >= 2:
                if raw_scores[-1] > raw_scores[0]:
                    trend = "↑ improving trend"
                elif raw_scores[-1] < raw_scores[0]:
                    trend = "↓ declining trend"
                else:
                    trend = "→ stable"
            st.caption(f"→ Average: {avg:.1f}/100 · {len(raw_scores)} score(s) entered {trend}")

        col1, col2 = st.columns(2)
        with col1:
            attendance_rate = st.slider(
                "Your attendance rate for this subject (%)",
                min_value=0, max_value=100, value=80, step=5,
                help="Every 10% drop in attendance correlates with ~3 fewer exam points (Credé et al. 2010).",
            )
            att_label = "Critical" if attendance_rate < 50 else \
                        "Concerning" if attendance_rate < 70 else "Good"
            st.caption(f"→ {att_label} — estimated score penalty: {max(0, (80 - attendance_rate) * 0.3):.1f} pts")

        with col2:
            self_understanding = st.slider(
                "How well do you truly understand the material? (1 = very confused; 10 = I could teach it)",
                min_value=1.0, max_value=10.0, value=6.0, step=0.5,
                help="This will be calibrated against your actual scores — the model corrects for overconfidence.",
            )

        # ── BLOCK 5: Physical & Mental State ─────────────────
        section_header("05 · Your Physical & Mental State", "Your body and mind directly affect your ability to learn and retain")

        col1, col2, col3 = st.columns(3)
        with col1:
            avg_sleep_hours = st.slider(
                "Average nightly sleep this week (hours)",
                min_value=2.0, max_value=12.0, value=7.0, step=0.5,
                help="Sleep is when memory consolidation happens. Under 6 hours significantly impairs next-day retention.",
            )
            sleep_label = "Insufficient" if avg_sleep_hours < 6 else \
                          "Borderline" if avg_sleep_hours < 7 else "Adequate"
            st.caption(f"→ {sleep_label}")

        with col2:
            sleep_quality = st.slider(
                "Sleep quality (1 = restless/interrupted; 10 = deep, restorative)",
                min_value=1.0, max_value=10.0, value=6.0, step=1.0,
            )

        with col3:
            stress_level = st.slider(
                "Stress level related to this exam (1 = calm; 10 = overwhelmed)",
                min_value=1.0, max_value=10.0, value=5.0, step=1.0,
                help="Chronic high stress (>7) physically impairs memory encoding and retrieval.",
            )
            stress_label = "Low" if stress_level <= 3 else "Moderate" if stress_level <= 6 else "High — concerning"
            st.caption(f"→ {stress_label}")

        energy_level = st.slider(
            "Your typical daily energy level this week (1 = exhausted; 10 = fully energised)",
            min_value=1.0, max_value=10.0, value=6.0, step=1.0,
        )

        # ── BLOCK 6: Support & Resources ─────────────────────
        section_header("06 · Support & Learning Resources", "External resources and social learning significantly boost outcomes")

        col1, col2, col3 = st.columns(3)
        with col1:
            has_study_group = st.checkbox(
                "I study with a group or study partner",
                help="Social learning improves accountability and exposes you to different problem-solving approaches.",
            )
        with col2:
            asks_questions_in_class = st.checkbox(
                "I ask questions in class when I don't understand",
                help="Active class participation correlates with significantly better exam performance.",
            )
        with col3:
            uses_additional_resources = st.checkbox(
                "I use resources beyond the course (books, videos, tutoring)",
                help="Access to multiple explanations helps when the main course material is unclear.",
            )

        # ── BLOCK 7: Confidence ──────────────────────────────
        section_header("07 · Self-Assessment", "Your honest opinion of where you stand")

        subjective_confidence = st.slider(
            "Overall confidence going into this exam (1 = not at all ready; 10 = fully confident)",
            min_value=1.0, max_value=10.0, value=6.0, step=0.5,
            help="This is compared against your objective data to detect and correct overconfidence or excessive self-doubt.",
        )

        conf_label = "Low confidence" if subjective_confidence < 4 else \
                     "Moderate confidence" if subjective_confidence < 7 else "High confidence"
        st.caption(f"→ {conf_label} — the model will calibrate this against your actual data")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── SUBMIT ───────────────────────────────────────────
        col_l, col_m, col_r = st.columns([2, 1.5, 2])
        with col_m:
            submitted = st.form_submit_button(
                "▶  ANALYSE MY RISK",
                use_container_width=True,
            )

        if submitted:
            if not subject_name.strip():
                st.error("Please enter the subject name before running the analysis.")
                return

            inp = SubjectInput(
                subject_name=subject_name.strip(),
                subject_type=subject_type,
                weekly_study_hours=weekly_study_hours,
                study_sessions_per_week=study_sessions_per_week,
                study_quality=study_quality,
                days_until_exam=int(days_until_exam),
                self_understanding=self_understanding,
                syllabus_coverage=float(syllabus_coverage),
                exercises_done=float(exercises_done),
                uses_past_papers=uses_past_papers,
                past_scores=raw_scores,
                attendance_rate=float(attendance_rate),
                avg_sleep_hours=avg_sleep_hours,
                sleep_quality=sleep_quality,
                stress_level=stress_level,
                energy_level=energy_level,
                has_study_group=has_study_group,
                asks_questions_in_class=asks_questions_in_class,
                uses_additional_resources=uses_additional_resources,
                subjective_confidence=subjective_confidence,
            )

            with st.spinner("Running risk analysis…"):
                result = compute_risk(inp)

            st.session_state.result = result
            st.session_state.show_results = True
            st.session_state.page = "results"
            st.rerun()


# ─────────────────────────────────────────────────────────────
# RESULTS PAGE
# ─────────────────────────────────────────────────────────────

def render_results(result: RiskResult):

    # ── TOP NAVIGATION ────────────────────────────────────────
    col_back, col_title, col_spacer = st.columns([1, 3, 1])
    with col_back:
        if st.button("← BACK TO FORM"):
            st.session_state.show_results = False
            st.session_state.page = "form"
            st.rerun()
    with col_title:
        st.markdown(
            f'<div style="text-align:center">'
            f'<span style="color:#f0c040;font-size:14px;font-weight:700;letter-spacing:.08em">'
            f'{result.subject_name.upper()}</span>'
            f'<span style="color:#444;font-size:11px;margin-left:10px">/ RISK ANALYSIS REPORT</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr style="border-color:#1e1e1e;margin:12px 0 24px">', unsafe_allow_html=True)

    # ── SECTION 1: VERDICT ────────────────────────────────────
    section_header("THE VERDICT", "What the model says, in plain language")

    col_gauge, col_verdict = st.columns([1, 2], gap="large")

    with col_gauge:
        st.plotly_chart(
            risk_gauge(result.risk_score, result.risk_tier, result.risk_tier_color),
            use_container_width=True, config={"displayModeBar": False},
        )
        st.plotly_chart(
            pass_probability_bar(result.pass_probability),
            use_container_width=True, config={"displayModeBar": False},
        )

    with col_verdict:
        tier_color = TIER_COLORS[result.risk_tier]
        card(
            f'<div style="margin-bottom:10px">'
            f'<span style="color:{tier_color};font-size:22px;font-weight:700;letter-spacing:.06em">'
            f'{result.risk_tier.upper()} RISK</span>'
            f'<span style="color:#444;font-size:11px;margin-left:12px">Score: {result.risk_score:.0f} / 100</span>'
            f'</div>'
            f'<p style="color:#cccccc;font-size:13px;line-height:1.8">{result.verdict_narrative}</p>',
            border_color=tier_color,
        )

        # 4 quick metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Predicted Score", f"{result.predicted_score:.0f}/100",
                  delta=f"{result.predicted_score - 50:+.0f} vs pass",
                  delta_color="normal")
        m2.metric("Pass Probability", f"{result.pass_probability*100:.0f}%")
        days_str = result.verdict_narrative.split('days remaining')[0].split('With ')[-1].strip() if 'days remaining' in result.verdict_narrative else "—"
        m3.metric("Days Remaining", days_str)
        m4.metric("Momentum", result.preparation_momentum)

    # ── SECTION 2: HOW EACH FACTOR CONTRIBUTES ───────────────
    section_header(
        "RISK BREAKDOWN — WHAT IS DRIVING YOUR SCORE",
        "Each factor below is an independently measured dimension of your preparation. "
        "Read them in order — the first one is your biggest risk."
    )

    col_decomp, col_radar = st.columns([1, 1], gap="large")

    with col_decomp:
        st.plotly_chart(
            risk_decomposition_chart(result.risk_decomposition),
            use_container_width=True, config={"displayModeBar": False},
        )
        st.markdown(
            '<p style="color:#555;font-size:10px;margin-top:4px">'
            'Bars show what % of your total risk each factor is responsible for. '
            'Red = major risk driver. Green = well managed.</p>',
            unsafe_allow_html=True,
        )

    with col_radar:
        st.plotly_chart(
            factor_radar(result.factor_radar),
            use_container_width=True, config={"displayModeBar": False},
        )

    # ── SECTION 3: FACTOR DETAIL CARDS ───────────────────────
    section_header(
        "FACTOR-BY-FACTOR ANALYSIS",
        "Every metric explained — what it is, why it matters, and what your score means for you"
    )

    for factor in result.factors:
        status_color = STATUS_COLORS_CSS[factor.status]
        border = status_color if factor.status != "safe" else "#2a2a2a"
        icon = STATUS_ICONS[factor.status]

        with st.expander(
            f"{icon}  {factor.plain_label.upper()}  —  Score: {factor.normalised:.0f}/100  "
            f"({factor.status.upper()})  ·  Weight: {factor.weight*100:.0f}% of model",
            expanded=(factor.status == "critical"),
        ):
            c1, c2 = st.columns([2, 1])

            with c1:
                st.markdown(
                    f'<div style="margin-bottom:10px">'
                    f'<span style="color:#666;font-size:10px;letter-spacing:.1em;text-transform:uppercase">What this measures</span><br>'
                    f'<span style="color:#cccccc;font-size:12px">{factor.what_it_measures}</span>'
                    f'</div>'
                    f'<div style="margin-bottom:10px">'
                    f'<span style="color:#666;font-size:10px;letter-spacing:.1em;text-transform:uppercase">Why it matters</span><br>'
                    f'<span style="color:#cccccc;font-size:12px">{factor.why_it_matters}</span>'
                    f'</div>'
                    f'<div style="background:#111;border-left:3px solid {status_color};padding:10px 14px;border-radius:0 2px 2px 0;margin-bottom:10px">'
                    f'<span style="color:#666;font-size:10px;letter-spacing:.1em;text-transform:uppercase">Your result</span><br>'
                    f'<span style="color:#eeeeee;font-size:12px">{factor.your_result}</span>'
                    f'</div>'
                    f'<div style="background:#0f1a10;border:1px solid #1a3020;padding:10px 14px;border-radius:2px">'
                    f'<span style="color:#3db87a;font-size:10px;letter-spacing:.1em;text-transform:uppercase">What to do</span><br>'
                    f'<span style="color:#cccccc;font-size:12px">{factor.advice}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            with c2:
                # Score bar
                bar_pct = int(factor.normalised)
                bar_color = status_color
                st.markdown(
                    f'<div style="background:#111;border:1px solid #222;border-radius:3px;padding:14px;text-align:center">'
                    f'<div style="color:{bar_color};font-size:36px;font-weight:700;font-family:Courier New">'
                    f'{factor.normalised:.0f}</div>'
                    f'<div style="color:#444;font-size:9px;letter-spacing:.1em;margin-bottom:10px">OUT OF 100</div>'
                    f'<div style="background:#222;height:6px;border-radius:3px;overflow:hidden">'
                    f'<div style="background:{bar_color};height:100%;width:{bar_pct}%;border-radius:3px"></div>'
                    f'</div>'
                    f'<div style="display:flex;justify-content:space-between;margin-top:3px">'
                    f'<span style="color:#333;font-size:9px">0</span>'
                    f'<span style="color:#333;font-size:9px">100</span>'
                    f'</div>'
                    f'<div style="margin-top:12px;padding:4px 8px;background:{status_color}22;'
                    f'border:1px solid {status_color}44;border-radius:2px;'
                    f'color:{status_color};font-size:10px;letter-spacing:.08em;font-weight:700">'
                    f'{factor.status.upper()}</div>'
                    f'<div style="margin-top:8px;color:#555;font-size:10px">'
                    f'Weight in model: {factor.weight*100:.0f}%</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── SECTION 4: PREPARATION PROFILE ───────────────────────
    section_header(
        "PREPARATION PROFILE",
        "Your scores across all preparation dimensions — anything below 60 is a gap"
    )

    st.plotly_chart(
        preparation_bars(result.preparation_profile),
        use_container_width=True, config={"displayModeBar": False},
    )

    st.markdown(
        '<p style="color:#555;font-size:10px">'
        'The dotted line at 60 marks the minimum recommended score for each dimension. '
        'Bars below this line represent active risk. '
        'Green = safe · Gold = needs attention · Red = critical gap.</p>',
        unsafe_allow_html=True,
    )

    # ── SECTION 5: SCORE TIMELINE ─────────────────────────────
    if len(result.score_timeline) > 1:
        section_header(
            "SCORE HISTORY & PREDICTION",
            "Your past performance trend — and where the model estimates you will land"
        )
        st.plotly_chart(
            score_timeline_chart(result.score_timeline, result.subject_name),
            use_container_width=True, config={"displayModeBar": False},
        )
        st.markdown(
            '<p style="color:#555;font-size:10px">'
            'The diamond marker is the model\'s predicted score for the upcoming exam, '
            'computed from a weighted combination of your trend, understanding score, '
            'coverage, and practice level. It is not a guarantee — it is a projection based on current data.</p>',
            unsafe_allow_html=True,
        )

    # ── SECTION 6: HOW THE MODEL WORKS ───────────────────────
    with st.expander("◎  How this model calculates your risk — full methodology"):
        st.markdown("""
**How the risk score is computed**

The risk score is a weighted composite of 8 independent factors. Each factor is computed from your inputs using documented formulas, then normalised to a 0–100 scale where 100 = best possible.

| Factor | Weight | How it is computed |
|---|---|---|
| Study Volume | 18% | Weekly hours vs recommended for subject type |
| Study Quality | 16% | Focus rating × session frequency bonus (spacing effect) |
| Track Record | 15% | Average past score + linear trend extrapolation |
| Programme Coverage | 14% | Syllabus % × 0.6 + exercises % × 0.4 + past paper bonus |
| Understanding | 13% | Self-assessed understanding, calibrated against past scores |
| Class Engagement | 9% | Attendance % + participation signals |
| Physical Recovery | 8% | Sleep score minus stress penalty |
| Active Practice | 7% | Exercise completion + past papers + external resources |

**Risk score formula**

```
preparation_score = Σ (factor_score × weight)
base_risk = 100 − preparation_score
risk_score = base_risk × time_pressure_modifier
```

**Pass probability formula (logistic)**

```
logit = −0.12 × (risk_score − 50)
pass_probability = 1 / (1 + e^(−logit))
```

This maps the linear risk score to a probability bounded between 0 and 1, following the same functional form as logistic regression models used in educational research.

**Predicted score**

```
predicted_score = past_record × 0.35 + understanding × 0.20
                + coverage × 0.18 + study_volume × 0.12
                + practice × 0.10 + attendance × 0.05
```

Blended with trend extrapolation (40% weight) when past scores are available.

**Research foundations:** Credé & Kuncel (2008), Cepeda et al. (2006), Karpicke & Roediger (2008), Walker (2017), Duckworth et al. (2007), Pilcher & Walters (1997).
        """)

    # ── SECTION 7: ACTION PLAN ────────────────────────────────
    section_header(
        "YOUR PRIORITY ACTION PLAN",
        "Three actions, ranked by estimated impact — derived directly from your weakest factors"
    )

    for action in result.action_plan:
        priority = action["priority"]
        impact_color = RED if priority == 1 else GOLD if priority == 2 else "#4a9ee8"
        card(
            f'<div style="display:flex;align-items:flex-start;gap:14px">'
            f'<div style="color:{impact_color};font-size:28px;font-weight:700;font-family:Courier New;'
            f'line-height:1;flex-shrink:0;width:30px">0{priority}</div>'
            f'<div>'
            f'<div style="color:#eeeeee;font-size:13px;font-weight:700;margin-bottom:5px">'
            f'{action["area"].upper()} — {action["action"]}</div>'
            f'<div style="color:#888;font-size:11px;line-height:1.7">{action["reason"]}</div>'
            f'<div style="margin-top:8px;color:{impact_color};font-size:10px;letter-spacing:.08em">'
            f'CURRENT SCORE: {action["current_score"]:.0f}/100 · ESTIMATED IMPACT: {action["impact"].upper()}</div>'
            f'</div>'
            f'</div>',
            border_color=impact_color,
        )

    # ── FOOTER ────────────────────────────────────────────────
    st.markdown(
        '<div style="border-top:1px solid #1e1e1e;margin-top:32px;padding-top:16px;'
        'color:#333;font-size:10px;text-align:center">'
        'SubjectRisk · Predictions are statistical estimates, not guarantees. '
        'Model based on peer-reviewed research in educational psychology. '
        'Results are only as accurate as the data you entered.</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────────────────────

if st.session_state.show_results and st.session_state.result:
    st.session_state.page = "results"

if st.session_state.page == "results" and st.session_state.result:
    render_results(st.session_state.result)
elif st.session_state.page == "form":
    render_form()
else:
    render_landing()
