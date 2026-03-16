"""
charts.py
=========
Responsibility: Build all interactive visualizations for the dashboard
using Plotly Graph Objects.

Rules for this module:
- Only receives DataFrames or dicts (output of metrics.py)
- Only returns Plotly figures (go.Figure)
- No business logic, no API calls, no Streamlit
- Consistent color palette across all charts
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ─── Color palette by pitch type ──────────────────────────────────────────────
# Consistent colors used across ALL charts in the dashboard
PITCH_COLORS = {
    "FF": "#E63946",  # 4-Seam Fastball  — red
    "SI": "#F4845F",  # Sinker           — reddish orange
    "FC": "#F4A261",  # Cutter           — orange
    "SL": "#2A9D8F",  # Slider           — teal
    "CH": "#457B9D",  # Changeup         — medium blue
    "CU": "#1D3557",  # Curveball        — dark blue
    "FS": "#8338EC",  # Splitter         — violet
    "ST": "#06D6A0",  # Sweeper          — mint green
    "KC": "#118AB2",  # Knuckle Curve    — blue
    "KN": "#FFB703",  # Knuckleball      — yellow
}
DEFAULT_COLOR = "#AAAAAA"
BACKGROUND    = "rgba(0,0,0,0)"    # transparent — Streamlit handles the background
GRID_COLOR    = "rgba(200,200,200,0.3)"
FONT_FAMILY   = "Inter, Arial, sans-serif"


def _color(pt: str) -> str:
    return PITCH_COLORS.get(pt, DEFAULT_COLOR)


def _color_list(series: pd.Series) -> list:
    return [_color(pt) for pt in series]


def _base_layout(fig: go.Figure, title: str = "") -> go.Figure:
    """Applies the consistent base layout to any figure."""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, family=FONT_FAMILY, color="#1A3C5E"),
            x=0,
        ),
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        font=dict(family=FONT_FAMILY, color="#333333"),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#DDDDDD",
            borderwidth=1,
        ),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    )
    return fig


# ─── 1. Horizontal bars: Usage Distribution ───────────────────────────────────

def chart_pitch_usage(metrics_df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart showing the usage % of each pitch type.
    Answers: What is this pitcher's full arsenal?
    """
    if metrics_df.empty:
        return go.Figure()

    df = metrics_df.sort_values("uso_pct", ascending=True)

    fig = go.Figure(go.Bar(
        x=df["uso_pct"],
        y=df["pitch_name_clean"],
        orientation="h",
        marker_color=_color_list(df["pitch_type"]),
        text=df["uso_pct"].apply(lambda x: f"{x}%"),
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Usage: %{x:.1f}%<br>"
            "Pitches: %{customdata}<extra></extra>"
        ),
        customdata=df["count"],
    ))

    fig = _base_layout(fig, "Usage Distribution by Pitch Type")
    fig.update_layout(
        xaxis_title="Usage (%)",
        yaxis_title="",
        showlegend=False,
        height=max(250, len(df) * 55),
        xaxis=dict(range=[0, df["uso_pct"].max() * 1.2], gridcolor=GRID_COLOR),
    )
    return fig


# ─── 2. Grouped bars: Effectiveness (Whiff + Called Strike) ───────────────────

def chart_effectiveness(metrics_df: pd.DataFrame) -> go.Figure:
    """
    Grouped bar chart comparing whiff_rate and called_strike_pct by pitch type.
    Answers: Which pitch is the hardest to hit?
    """
    if metrics_df.empty:
        return go.Figure()

    df = metrics_df.dropna(subset=["whiff_rate"]).sort_values("uso_pct", ascending=False)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Whiff Rate %",
        x=df["pitch_name_clean"],
        y=df["whiff_rate"],
        marker_color=_color_list(df["pitch_type"]),
        opacity=0.9,
        hovertemplate="<b>%{x}</b><br>Whiff Rate: %{y:.1f}%<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="Called Strike %",
        x=df["pitch_name_clean"],
        y=df["called_strike_pct"],
        marker_color=_color_list(df["pitch_type"]),
        opacity=0.4,
        hovertemplate="<b>%{x}</b><br>Called Strike: %{y:.1f}%<extra></extra>",
    ))

    fig = _base_layout(fig, "Effectiveness by Pitch Type")
    fig.update_layout(
        barmode="group",
        yaxis_title="Percentage (%)",
        xaxis_title="",
        height=400,
    )
    return fig


# ─── 3. Heatmap: Dominant Pitch by Balls-Strikes Count ────────────────────────

def chart_count_heatmap(count_df: pd.DataFrame) -> go.Figure:
    """
    4x3 heatmap (balls x strikes) showing the dominant pitch
    and its usage % in each count.
    Answers: What does this pitcher throw in a 3-2 count?

    Parameters
    ----------
    count_df : pd.DataFrame
        Output of metrics.get_dominant_pitch_per_count()
    """
    if count_df.empty:
        return go.Figure()

    balls_range   = [0, 1, 2, 3]
    strikes_range = [0, 1, 2]

    # Matrices for text, numeric value, and hover
    z_vals = [[0.0] * len(balls_range) for _ in strikes_range]
    z_text = [[""]  * len(balls_range) for _ in strikes_range]
    hover  = [[""]  * len(balls_range) for _ in strikes_range]

    for _, row in count_df.iterrows():
        b = int(row["balls"])
        s = int(row["strikes"])
        if b in balls_range and s in strikes_range:
            bi = balls_range.index(b)
            si = strikes_range.index(s)
            pct   = row.get("pct_in_count", 0)
            pt    = row.get("pitch_type", "")
            pname = row.get("pitch_name_clean", pt)
            z_vals[si][bi] = float(pct)
            z_text[si][bi] = f"<b>{pt}</b><br>{pct:.0f}%"
            hover[si][bi]  = f"Count {b}-{s}<br>{pname}<br>Usage in count: {pct:.1f}%"

    fig = go.Figure(go.Heatmap(
        z=z_vals,
        x=[f"Balls {b}" for b in balls_range],
        y=[f"Strikes {s}" for s in strikes_range],
        text=z_text,
        texttemplate="%{text}",
        colorscale=[
            [0.0, "#F0F4FA"],
            [0.5, "#7EB8D4"],
            [1.0, "#1A3C5E"],
        ],
        showscale=True,
        colorbar=dict(title="Usage %", tickfont=dict(size=11)),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover,
    ))

    fig = _base_layout(fig, "Dominant Pitch by Count (Balls-Strikes)")
    fig.update_layout(
        height=320,
        xaxis=dict(side="top", gridcolor=GRID_COLOR),
        yaxis=dict(autorange="reversed", gridcolor=GRID_COLOR),
    )
    return fig


# ─── 4. Grouped bars: Matchup — Left vs Right ─────────────────────────────────

def chart_matchup(matchup_df: pd.DataFrame, metric: str = "whiff_rate") -> go.Figure:
    """
    Grouped bar chart L vs R by pitch type.
    Answers: Is the slider better against left-handed or right-handed batters?

    Parameters
    ----------
    matchup_df : pd.DataFrame
        Output of metrics.get_matchup_metrics()
    metric : str
        "whiff_rate" or "uso_pct"
    """
    if matchup_df.empty:
        return go.Figure()

    label_map = {"whiff_rate": "Whiff Rate (%)", "uso_pct": "Usage (%)"}
    title_map = {
        "whiff_rate": "Whiff Rate by Batter Handedness",
        "uso_pct":    "Usage (%) by Batter Handedness",
    }

    # Order pitches by average usage
    pitch_order = (
        matchup_df.groupby("pitch_name_clean")["uso_pct"]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )

    left_df  = matchup_df[matchup_df["stand"] == "L"]
    right_df = matchup_df[matchup_df["stand"] == "R"]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="vs Left (L)",
        x=left_df["pitch_name_clean"],
        y=left_df[metric],
        marker_color="#E63946",
        opacity=0.85,
        hovertemplate="<b>%{x}</b><br>vs Left: %{y:.1f}%<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="vs Right (R)",
        x=right_df["pitch_name_clean"],
        y=right_df[metric],
        marker_color="#457B9D",
        opacity=0.85,
        hovertemplate="<b>%{x}</b><br>vs Right: %{y:.1f}%<extra></extra>",
    ))

    fig = _base_layout(fig, title_map.get(metric, metric))
    fig.update_layout(
        barmode="group",
        yaxis_title=label_map.get(metric, metric),
        xaxis=dict(categoryorder="array", categoryarray=pitch_order),
        height=400,
    )
    return fig


# ─── 5. Scatter: Pitch Location in the Strike Zone ────────────────────────────

def chart_pitch_location(location_df: pd.DataFrame) -> go.Figure:
    """
    Scatter plot of plate_x vs plate_z, colored by pitch type.
    Draws the strike zone as a visual reference.
    Answers: What zones does this pitcher target with each pitch type?

    Parameters
    ----------
    location_df : pd.DataFrame
        Output of metrics.get_location_data()
    """
    if location_df.empty:
        return go.Figure()

    fig = go.Figure()

    # ── Standard MLB strike zone ──
    # Horizontal: ±0.83 ft | Vertical: 1.5 – 3.5 ft
    fig.add_shape(
        type="rect",
        x0=-0.83, x1=0.83, y0=1.5, y1=3.5,
        line=dict(color="#1A3C5E", width=2, dash="dash"),
        fillcolor="rgba(0,0,0,0)",
    )

    # ── Home plate (visual reference) ──
    fig.add_shape(
        type="rect",
        x0=-0.71, x1=0.71, y0=0.0, y1=0.15,
        line=dict(color="#888888", width=1),
        fillcolor="rgba(200,200,200,0.3)",
    )

    # ── One trace per pitch type → interactive legend ──
    for pt in location_df["pitch_type"].unique():
        subset = location_df[location_df["pitch_type"] == pt]
        pname  = subset["pitch_name_clean"].iloc[0]

        fig.add_trace(go.Scatter(
            x=subset["plate_x"],
            y=subset["plate_z"],
            mode="markers",
            name=pname,
            marker=dict(
                color=_color(pt),
                size=6,
                opacity=0.55,
                line=dict(width=0.3, color="white"),
            ),
            hovertemplate=(
                f"<b>{pname}</b><br>"
                "Horizontal: %{x:.2f} ft<br>"
                "Height: %{y:.2f} ft<br>"
                "Outcome: %{customdata}<extra></extra>"
            ),
            customdata=subset["description"],
        ))

    fig = _base_layout(fig, "Pitch Location in the Strike Zone")
    fig.update_layout(
        xaxis=dict(
            title="Horizontal (feet from plate center)",
            range=[-2.5, 2.5],
            zeroline=True,
            zerolinecolor="#CCCCCC",
            gridcolor=GRID_COLOR,
        ),
        yaxis=dict(
            title="Height (feet from ground)",
            range=[-0.5, 5.5],
            zeroline=False,
            gridcolor=GRID_COLOR,
        ),
        height=520,
        legend=dict(
            title="Pitch Type",
            itemclick="toggle",
            itemdoubleclick="toggleothers",
        ),
    )

    fig.add_annotation(
        x=0.83, y=3.5,
        text="Strike Zone",
        showarrow=False,
        font=dict(size=10, color="#1A3C5E"),
        xanchor="left",
        yanchor="bottom",
        xshift=5,
    )

    return fig


# ─── 6. Lollipop: Average Velocity by Pitch Type ──────────────────────────────

def chart_velocity(metrics_df: pd.DataFrame) -> go.Figure:
    """
    Lollipop chart showing average velocity by pitch type.
    Answers: How much faster is the fastball than the slider?
    """
    if metrics_df.empty:
        return go.Figure()

    df = metrics_df.dropna(subset=["avg_velocity"]).sort_values("avg_velocity", ascending=True)
    v_min = df["avg_velocity"].min() - 3

    fig = go.Figure()

    # Horizontal lines (lollipop stems)
    for _, row in df.iterrows():
        fig.add_shape(
            type="line",
            x0=v_min, x1=row["avg_velocity"],
            y0=row["pitch_name_clean"], y1=row["pitch_name_clean"],
            line=dict(color="#DDDDDD", width=1.5),
        )

    # Points with label
    fig.add_trace(go.Scatter(
        x=df["avg_velocity"],
        y=df["pitch_name_clean"],
        mode="markers+text",
        marker=dict(
            color=_color_list(df["pitch_type"]),
            size=14,
            line=dict(width=1, color="white"),
        ),
        text=df["avg_velocity"].apply(lambda v: f"{v:.1f}"),
        textposition="middle right",
        textfont=dict(size=11, color="#333333"),
        hovertemplate="<b>%{y}</b><br>Velocity: %{x:.1f} MPH<extra></extra>",
        showlegend=False,
    ))

    fig = _base_layout(fig, "Average Velocity by Pitch Type (MPH)")
    fig.update_layout(
        xaxis=dict(
            title="Velocity (MPH)",
            range=[v_min - 2, df["avg_velocity"].max() + 5],
            gridcolor=GRID_COLOR,
        ),
        yaxis_title="",
        height=max(250, len(df) * 55),
        showlegend=False,
    )
    return fig