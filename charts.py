"""
charts.py
=========
Responsabilidad: Construir todas las visualizaciones interactivas
del dashboard usando Plotly Express y Plotly Graph Objects.

Reglas de este módulo:
- Solo recibe DataFrames o dicts (salida de metrics.py)
- Solo devuelve figuras de Plotly (go.Figure)
- Sin lógica de negocio, sin llamadas a APIs, sin Streamlit
- Paleta de colores consistente en todas las gráficas
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ─── Paleta de colores por pitch type ─────────────────────────────────────────
# Colores consistentes en TODAS las gráficas del dashboard
PITCH_COLORS = {
    "FF": "#E63946",  # 4-Seam Fastball  — rojo
    "SI": "#F4845F",  # Sinker           — naranja rojizo
    "FC": "#F4A261",  # Cutter           — naranja
    "SL": "#2A9D8F",  # Slider           — verde azulado
    "CH": "#457B9D",  # Changeup         — azul medio
    "CU": "#1D3557",  # Curveball        — azul oscuro
    "FS": "#8338EC",  # Splitter         — violeta
    "ST": "#06D6A0",  # Sweeper          — verde menta
    "KC": "#118AB2",  # Knuckle Curve    — azul
    "KN": "#FFB703",  # Knuckleball      — amarillo
}
DEFAULT_COLOR  = "#AAAAAA"
BACKGROUND     = "rgba(0,0,0,0)"   # transparente — Streamlit maneja el fondo
GRID_COLOR     = "rgba(200,200,200,0.3)"
FONT_FAMILY    = "Inter, Arial, sans-serif"


def _color(pt: str) -> str:
    return PITCH_COLORS.get(pt, DEFAULT_COLOR)


def _color_list(series: pd.Series) -> list:
    return [_color(pt) for pt in series]


def _base_layout(fig: go.Figure, title: str = "") -> go.Figure:
    """Aplica el layout base consistente a cualquier figura."""
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


# ─── 1. Barras horizontales: Distribución de Uso ──────────────────────────────

def chart_pitch_usage(metrics_df: pd.DataFrame) -> go.Figure:
    """
    Barras horizontales con el % de uso de cada tipo de pitcheo.
    Responde: ¿Cuál es el arsenal completo de este pitcher?
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
            "Uso: %{x:.1f}%<br>"
            "Lanzamientos: %{customdata}<extra></extra>"
        ),
        customdata=df["count"],
    ))

    fig = _base_layout(fig, "Distribución de Uso por Tipo de Pitcheo")
    fig.update_layout(
        xaxis_title="Uso (%)",
        yaxis_title="",
        showlegend=False,
        height=max(250, len(df) * 55),
        xaxis=dict(range=[0, df["uso_pct"].max() * 1.2], gridcolor=GRID_COLOR),
    )
    return fig


# ─── 2. Barras agrupadas: Efectividad (Whiff + Called Strike) ─────────────────

def chart_effectiveness(metrics_df: pd.DataFrame) -> go.Figure:
    """
    Barras agrupadas comparando whiff_rate y called_strike_pct por pitch type.
    Responde: ¿Cuál es el pitch más difícil de batear?
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

    fig = _base_layout(fig, "Efectividad por Tipo de Pitcheo")
    fig.update_layout(
        barmode="group",
        yaxis_title="Porcentaje (%)",
        xaxis_title="",
        height=400,
    )
    return fig


# ─── 3. Heatmap: Pitch Dominante por Conteo Balls-Strikes ─────────────────────

def chart_count_heatmap(count_df: pd.DataFrame) -> go.Figure:
    """
    Heatmap 4×3 (balls × strikes) mostrando el pitch dominante
    y su % de uso en cada conteo.
    Responde: ¿En 3-2 qué lanza este pitcher?

    Parameters
    ----------
    count_df : pd.DataFrame
        Salida de metrics.get_dominant_pitch_per_count()
    """
    if count_df.empty:
        return go.Figure()

    balls_range   = [0, 1, 2, 3]
    strikes_range = [0, 1, 2]

    # Matrices para texto, valor numérico y hover
    z_vals  = [[0.0] * len(balls_range) for _ in strikes_range]
    z_text  = [[""]  * len(balls_range) for _ in strikes_range]
    hover   = [[""]  * len(balls_range) for _ in strikes_range]

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
            hover[si][bi]  = f"Conteo {b}-{s}<br>{pname}<br>Uso en conteo: {pct:.1f}%"

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
        colorbar=dict(title="Uso %", tickfont=dict(size=11)),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover,
    ))

    fig = _base_layout(fig, "Pitch Dominante por Conteo (Balls-Strikes)")
    fig.update_layout(
        height=320,
        xaxis=dict(side="top", gridcolor=GRID_COLOR),
        yaxis=dict(autorange="reversed", gridcolor=GRID_COLOR),
    )
    return fig


# ─── 4. Barras agrupadas: Matchup Zurdo vs Diestro ────────────────────────────

def chart_matchup(matchup_df: pd.DataFrame, metric: str = "whiff_rate") -> go.Figure:
    """
    Barras agrupadas L vs R por pitch type.
    Responde: ¿El slider es mejor contra zurdos o diestros?

    Parameters
    ----------
    matchup_df : pd.DataFrame
        Salida de metrics.get_matchup_metrics()
    metric : str
        "whiff_rate" o "uso_pct"
    """
    if matchup_df.empty:
        return go.Figure()

    label_map = {"whiff_rate": "Whiff Rate (%)", "uso_pct": "Uso (%)"}
    title_map = {
        "whiff_rate": "Whiff Rate por Mano del Bateador",
        "uso_pct":    "Uso (%) por Mano del Bateador",
    }

    # Orden de pitches por uso promedio
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
        name="vs Zurdo (L)",
        x=left_df["pitch_name_clean"],
        y=left_df[metric],
        marker_color="#E63946",
        opacity=0.85,
        hovertemplate="<b>%{x}</b><br>vs Zurdo: %{y:.1f}%<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="vs Diestro (R)",
        x=right_df["pitch_name_clean"],
        y=right_df[metric],
        marker_color="#457B9D",
        opacity=0.85,
        hovertemplate="<b>%{x}</b><br>vs Diestro: %{y:.1f}%<extra></extra>",
    ))

    fig = _base_layout(fig, title_map.get(metric, metric))
    fig.update_layout(
        barmode="group",
        yaxis_title=label_map.get(metric, metric),
        xaxis=dict(categoryorder="array", categoryarray=pitch_order),
        height=400,
    )
    return fig


# ─── 5. Scatter: Localización de Pitcheos en la Zona ─────────────────────────

def chart_pitch_location(location_df: pd.DataFrame) -> go.Figure:
    """
    Scatter plot plate_x vs plate_z, coloreado por pitch type.
    Dibuja el strike zone como referencia visual.
    Responde: ¿A qué zonas apunta este pitcher con cada tipo de pitcheo?

    Parameters
    ----------
    location_df : pd.DataFrame
        Salida de metrics.get_location_data()
    """
    if location_df.empty:
        return go.Figure()

    fig = go.Figure()

    # ── Strike zone estándar MLB ──
    # Horizontal: ±0.83 pies | Vertical: 1.5 – 3.5 pies
    fig.add_shape(
        type="rect",
        x0=-0.83, x1=0.83, y0=1.5, y1=3.5,
        line=dict(color="#1A3C5E", width=2, dash="dash"),
        fillcolor="rgba(0,0,0,0)",
    )

    # ── Home plate (referencia visual) ──
    fig.add_shape(
        type="rect",
        x0=-0.71, x1=0.71, y0=0.0, y1=0.15,
        line=dict(color="#888888", width=1),
        fillcolor="rgba(200,200,200,0.3)",
    )

    # ── Un trace por pitch type → leyenda interactiva ──
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
                "Vertical: %{y:.2f} ft<br>"
                "Resultado: %{customdata}<extra></extra>"
            ),
            customdata=subset["description"],
        ))

    fig = _base_layout(fig, "Localización de Pitcheos en la Zona")
    fig.update_layout(
        xaxis=dict(
            title="Horizontal (pies desde el centro del plato)",
            range=[-2.5, 2.5],
            zeroline=True,
            zerolinecolor="#CCCCCC",
            gridcolor=GRID_COLOR,
        ),
        yaxis=dict(
            title="Altura (pies desde el suelo)",
            range=[-0.5, 5.5],
            zeroline=False,
            gridcolor=GRID_COLOR,
        ),
        height=520,
        legend=dict(
            title="Tipo de Pitcheo",
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


# ─── 6. Lollipop: Velocidad promedio por Pitch Type ───────────────────────────

def chart_velocity(metrics_df: pd.DataFrame) -> go.Figure:
    """
    Gráfico tipo lollipop con la velocidad promedio por pitch type.
    Responde: ¿Cuánto más rápido es su fastball vs su slider?
    """
    if metrics_df.empty:
        return go.Figure()

    df = metrics_df.dropna(subset=["avg_velocity"]).sort_values("avg_velocity", ascending=True)
    v_min = df["avg_velocity"].min() - 3

    fig = go.Figure()

    # Líneas horizontales (tallo del lollipop)
    for _, row in df.iterrows():
        fig.add_shape(
            type="line",
            x0=v_min, x1=row["avg_velocity"],
            y0=row["pitch_name_clean"], y1=row["pitch_name_clean"],
            line=dict(color="#DDDDDD", width=1.5),
        )

    # Puntos con etiqueta
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
        hovertemplate="<b>%{y}</b><br>Velocidad: %{x:.1f} MPH<extra></extra>",
        showlegend=False,
    ))

    fig = _base_layout(fig, "Velocidad Promedio por Tipo de Pitcheo (MPH)")
    fig.update_layout(
        xaxis=dict(
            title="Velocidad (MPH)",
            range=[v_min - 2, df["avg_velocity"].max() + 5],
            gridcolor=GRID_COLOR,
        ),
        yaxis_title="",
        height=max(250, len(df) * 55),
        showlegend=False,
    )
    return fig
