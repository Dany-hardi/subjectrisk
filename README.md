# SubjectRisk — Exam Failure Prediction Engine

A Python/Streamlit application that collects student behavioural and academic
data for a specific subject and computes a statistically justified risk of
failing the upcoming exam — with every metric explained in plain language.

## Bloomberg Terminal aesthetic · Black & Gold · Courier New

---

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

---

## What It Does

1. **Data Collection** — A structured form collecting 20+ variables about study
   behaviour, academic record, physical state, and support resources — all
   specific to one subject and one exam.

2. **Risk Engine** — Computes 8 independent factors using documented formulas
   from educational psychology research. Each factor is normalised to 0–100
   and weighted by its empirical importance.

3. **Results Display** — Bloomberg Terminal-style dashboard showing:
   - Overall risk score (0–100) with animated gauge
   - Pass probability (logistic formula, 0–100%)
   - Predicted exam score (weighted regression model)
   - Risk decomposition bar chart (which factor contributes most)
   - Preparation radar chart (all 8 dimensions)
   - Factor-by-factor breakdown — what it measures, why it matters, your result
   - Score history & trajectory chart
   - Personalised 3-action priority plan

---

## The 8 Risk Factors

| Factor | Weight | Research Basis |
|---|---|---|
| Study Volume | 18% | NSSE 2019 — time-on-task baseline |
| Study Quality | 16% | Cepeda et al. 2006 — spacing effect |
| Track Record | 15% | Credé & Kuncel 2008 — best single predictor |
| Programme Coverage | 14% | Roediger & Karpicke 2006 — testing effect |
| Depth of Understanding | 13% | Calibrated against actual performance |
| Class Engagement | 9% | Credé et al. 2010 — 3 pts per 10% attendance |
| Physical Recovery | 8% | Walker 2017 — sleep & memory consolidation |
| Active Practice | 7% | Karpicke & Roediger 2008 — +50% retrieval |

---

## Architecture

```
subjectrisk/
├── app.py                   # Streamlit UI (form + results)
├── engine/
│   ├── risk_engine.py       # All statistical calculations
│   └── charts.py            # All Plotly visualisations
├── assets/
│   └── style.css            # Bloomberg Terminal CSS theme
└── requirements.txt
```

---

## Risk Score Formula

```
preparation_score = Σ (factor_score_i × weight_i)
base_risk         = 100 − preparation_score
risk_score        = base_risk × time_pressure_modifier
pass_probability  = 1 / (1 + e^(−0.12 × (risk_score − 50)))
```

All calculations are transparent and shown in the "How this model works"
section of the results page.
