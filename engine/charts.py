"""
SubjectRisk — Chart Engine
All Plotly figures. Bloomberg Terminal palette: black + yellow.
"""

from __future__ import annotations
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import math

# ─── BLOOMBERG PALETTE ───────────────────────────────────────
BG       = "#0a0a0a"
SURFACE  = "#111111"
CARD     = "#181818"
BORDER   = "#2a2a2a"
GOLD     = "#f0c040"
GOLD_DIM = "#c89a28"
GOLD_LOW = "rgba(240,192,64,0.12)"
DIM      = "#666666"
TEXT     = "#eeeeee"
TEXT2    = "#aaaaaa"
GREEN    = "#3db87a"
RED      = "#e05050"
ORANGE   = "#e08040"
BLUE     = "#4a9ee8"

STATUS_COLORS = {"safe": GREEN, "warning": GOLD, "critical": RED}

CHART_BASE = dict(
    paper_bgcolor=BG,
    plot_bgcolor=CARD,
    font=dict(family="Courier New, monospace", color=TEXT2, size=11),
    margin=dict(l=20, r=20, t=40, b=20),
)


def _grid_style():
    return dict(showgrid=True, gridcolor=BORDER, gridwidth=1,
                zeroline=False, showline=True, linecolor=BORDER)


# ─── 1. RISK GAUGE ───────────────────────────────────────────
def risk_gauge(risk_score: float, tier: str, tier_color: str) -> go.Figure:
    """Large animated gauge showing overall risk score."""

    # Color needle based on risk
    needle_color = tier_color

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        number=dict(
            suffix="/100",
            font=dict(size=42, color=GOLD, family="Courier New, monospace"),
        ),
        gauge=dict(
            axis=dict(
                range=[0, 100],
                tickwidth=1,
                tickcolor=BORDER,
                tickfont=dict(color=DIM, size=10),
                dtick=20,
            ),
            bar=dict(color=needle_color, thickness=0.25),
            bgcolor=SURFACE,
            borderwidth=1,
            bordercolor=BORDER,
            steps=[
                dict(range=[0, 25],  color="#0d2218"),
                dict(range=[25, 50], color="#2a2010"),
                dict(range=[50, 75], color="#2a1a0a"),
                dict(range=[75, 100], color="#2a0d0d"),
            ],
            threshold=dict(
                line=dict(color=needle_color, width=3),
                thickness=0.8,
                value=risk_score,
            ),
        ),
        title=dict(
            text=f"<b>{tier.upper()} RISK</b>",
            font=dict(size=13, color=tier_color, family="Courier New, monospace"),
        ),
        domain=dict(x=[0, 1], y=[0, 1]),
    ))

    fig.update_layout(
        **CHART_BASE,
        height=240,
        annotations=[
            dict(x=0.18, y=0.12, xref="paper", yref="paper",
                 text="SAFE", font=dict(color=GREEN, size=9), showarrow=False),
            dict(x=0.82, y=0.12, xref="paper", yref="paper",
                 text="CRITICAL", font=dict(color=RED, size=9), showarrow=False),
        ]
    )
    return fig


# ─── 2. FACTOR RADAR ─────────────────────────────────────────
def factor_radar(factor_radar_data: dict) -> go.Figure:
    """Radar / spider chart of all 8 preparation dimensions."""
    labels = list(factor_radar_data.keys())
    values = list(factor_radar_data.values())
    values_closed = values + [values[0]]
    labels_closed = labels + [labels[0]]

    # Benchmark line at 60 (minimum acceptable)
    benchmark = [60] * len(labels)
    benchmark_closed = benchmark + [benchmark[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=benchmark_closed, theta=labels_closed,
        fill=None, mode="lines",
        line=dict(color=BORDER, width=1, dash="dot"),
        name="Min. threshold (60)",
        showlegend=True,
    ))

    fig.add_trace(go.Scatterpolar(
        r=values_closed, theta=labels_closed,
        fill="toself",
        fillcolor=GOLD_LOW,
        mode="lines+markers",
        line=dict(color=GOLD, width=2),
        marker=dict(color=[STATUS_COLORS.get(
            "safe" if v >= 60 else "warning" if v >= 35 else "critical", GOLD
        ) for v in values + [values[0]]], size=7),
        name="Your profile",
        showlegend=True,
    ))

    fig.update_layout(
        **CHART_BASE,
        height=340,
        polar=dict(
            bgcolor=CARD,
            radialaxis=dict(
                visible=True, range=[0, 100],
                tickfont=dict(color=DIM, size=9),
                gridcolor=BORDER, linecolor=BORDER,
            ),
            angularaxis=dict(
                tickfont=dict(color=TEXT2, size=10),
                gridcolor=BORDER, linecolor=BORDER,
            ),
        ),
        legend=dict(
            x=0.5, y=-0.05, xanchor="center",
            font=dict(color=TEXT2, size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
        title=dict(text="Preparation Profile — All Dimensions",
                   font=dict(size=12, color=TEXT2), x=0.5, xanchor="center"),
    )
    return fig


# ─── 3. RISK DECOMPOSITION (horizontal bar) ──────────────────
def risk_decomposition_chart(decomp: dict) -> go.Figure:
    """Horizontal bar showing each factor's % contribution to total risk."""
    items = sorted(decomp.items(), key=lambda x: x[1], reverse=True)
    labels = [i[0] for i in items]
    values = [i[1] for i in items]

    # Color by contribution size
    colors = []
    for v in values:
        if v >= 20: colors.append(RED)
        elif v >= 12: colors.append(ORANGE)
        elif v >= 7: colors.append(GOLD)
        else: colors.append(GREEN)

    fig = go.Figure(go.Bar(
        y=labels, x=values,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in values],
        textfont=dict(color=TEXT, size=10, family="Courier New, monospace"),
        textposition="outside",
    ))

    fig.update_layout(
        **CHART_BASE,
        height=max(240, len(labels) * 38 + 60),
        xaxis=dict(**_grid_style(), title=dict(text="Contribution to risk (%)", font=dict(size=10, color=DIM)), range=[0, max(values) * 1.3]),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(color=TEXT2, size=11)),
        title=dict(text="Risk Decomposition — What Is Driving Your Score",
                   font=dict(size=12, color=TEXT2), x=0.5, xanchor="center"),
        showlegend=False,
    )
    return fig


# ─── 4. SCORE TIMELINE ───────────────────────────────────────
def score_timeline_chart(scores: list[float], subject: str) -> go.Figure:
    """Line chart of past scores + predicted next score."""
    n = len(scores)
    if n == 0:
        return go.Figure()

    x_past = list(range(1, n))
    y_past = scores[:-1]
    x_pred = n - 1
    y_pred = scores[-1]

    fig = go.Figure()

    if x_past:
        fig.add_trace(go.Scatter(
            x=x_past, y=y_past,
            mode="lines+markers",
            line=dict(color=GOLD, width=2),
            marker=dict(color=GOLD, size=7),
            name="Past scores",
        ))

    # Connector line to prediction
    fig.add_trace(go.Scatter(
        x=[x_past[-1] if x_past else 0, x_pred],
        y=[y_past[-1] if y_past else y_pred, y_pred],
        mode="lines",
        line=dict(color=DIM, width=1.5, dash="dot"),
        showlegend=False,
    ))

    # Predicted point
    pred_color = GREEN if y_pred >= 50 else RED
    fig.add_trace(go.Scatter(
        x=[x_pred], y=[y_pred],
        mode="markers+text",
        marker=dict(color=pred_color, size=12, symbol="diamond",
                    line=dict(color=TEXT, width=1.5)),
        text=[f"  Predicted: {y_pred:.0f}"],
        textfont=dict(color=pred_color, size=11),
        textposition="middle right",
        name=f"Predicted score",
    ))

    # Pass line at 50
    fig.add_hline(y=50, line_dash="dot", line_color=BORDER,
                  annotation_text="Pass threshold",
                  annotation_font=dict(color=DIM, size=9))

    fig.update_layout(
        **CHART_BASE,
        height=220,
        xaxis=dict(**_grid_style(), title=dict(text="Test #", font=dict(size=10, color=DIM)),
                   tickmode="linear", dtick=1),
        yaxis=dict(**_grid_style(), title=dict(text="Score / 100", font=dict(size=10, color=DIM)), range=[0, 105]),
        legend=dict(x=0.02, y=0.98, font=dict(color=TEXT2, size=10),
                    bgcolor="rgba(0,0,0,0)"),
        title=dict(text=f"{subject} — Score History & Prediction",
                   font=dict(size=12, color=TEXT2), x=0.5, xanchor="center"),
    )
    return fig


# ─── 5. PREPARATION BARS ─────────────────────────────────────
def preparation_bars(profile: dict) -> go.Figure:
    """Grouped bullet-style bars for each preparation dimension."""
    dims = list(profile.keys())
    vals = list(profile.values())
    colors = [GREEN if v >= 65 else GOLD if v >= 40 else RED for v in vals]

    fig = go.Figure()

    # Background bars (full width = 100)
    fig.add_trace(go.Bar(
        x=dims, y=[100] * len(dims),
        marker=dict(color=SURFACE, line=dict(width=0)),
        showlegend=False, hoverinfo="skip",
    ))

    # Value bars
    fig.add_trace(go.Bar(
        x=dims, y=vals,
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:.0f}" for v in vals],
        textfont=dict(color="#000", size=11, family="Courier New, monospace"),
        textposition="inside",
        name="Your score",
        showlegend=False,
    ))

    # Threshold line at 60
    fig.add_hline(y=60, line_dash="dot", line_color=BORDER,
                  annotation_text="Min. recommended (60)",
                  annotation_font=dict(color=DIM, size=9),
                  annotation_position="top right")

    fig.update_layout(
        **CHART_BASE,
        height=240,
        barmode="overlay",
        xaxis=dict(showgrid=False, showline=False,
                   tickfont=dict(color=TEXT2, size=10)),
        yaxis=dict(**_grid_style(), range=[0, 110],
                   tickfont=dict(color=DIM, size=9)),
        title=dict(text="Preparation Dimensions — Your Scores (out of 100)",
                   font=dict(size=12, color=TEXT2), x=0.5, xanchor="center"),
    )
    return fig


# ─── 6. PASS PROBABILITY GAUGE ───────────────────────────────
def pass_probability_bar(pass_prob: float) -> go.Figure:
    """Single horizontal progress bar for pass probability."""
    pct = round(pass_prob * 100, 1)
    color = GREEN if pct >= 70 else GOLD if pct >= 45 else RED

    fig = go.Figure(go.Bar(
        x=[pct], y=[""],
        orientation="h",
        marker=dict(color=color, line=dict(width=0)),
        text=[f"{pct:.0f}% chance of passing"],
        textfont=dict(color="#000" if color == GOLD else TEXT,
                      size=13, family="Courier New, monospace"),
        textposition="inside",
        showlegend=False,
    ))

    # Background
    fig.add_trace(go.Bar(
        x=[100 - pct], y=[""],
        orientation="h",
        marker=dict(color=SURFACE, line=dict(width=0)),
        showlegend=False, hoverinfo="skip",
    ))

    fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=CARD,
        font=dict(family="Courier New, monospace", color=TEXT2, size=11),
        height=80,
        barmode="stack",
        xaxis=dict(range=[0, 100], showgrid=False, showticklabels=False,
                   showline=False),
        yaxis=dict(showgrid=False, showline=False, showticklabels=False),
        margin=dict(l=10, r=10, t=10, b=10),
        shapes=[dict(type="line", x0=50, x1=50, y0=-0.5, y1=0.5,
                     line=dict(color=BORDER, width=1.5, dash="dot"),
                     xref="x", yref="y")],
    )
    return fig
