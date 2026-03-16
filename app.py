"""
app.py
======
Punto de entrada del dashboard Pitch Effectiveness Analyzer.
Conecta data_loader → metrics → charts en una interfaz Streamlit.

Ejecutar con:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd

from data_loader import load_pitcher_data, search_pitcher, validate_dataframe
from metrics import (
    get_summary_kpis,
    get_pitch_metrics,
    get_count_distribution,
    get_dominant_pitch_per_count,
    get_matchup_metrics,
    get_location_data,
)
from charts import (
    chart_pitch_usage,
    chart_effectiveness,
    chart_count_heatmap,
    chart_matchup,
    chart_pitch_location,
    chart_velocity,
)

# ─── Configuración de página ──────────────────────────────────────────────────

st.set_page_config(
    page_title="Pitch Analyzer | MLB Statcast",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS personalizado ────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* Reset y base */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Fondo principal oscuro */
.stApp {
    background-color: #0B1120;
    color: #E8EDF5;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #111827;
    border-right: 1px solid #1E2D45;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label {
    color: #9BAABB !important;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Títulos con Syne */
h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
}

/* Header principal */
.main-header {
    padding: 2rem 0 1.5rem 0;
    border-bottom: 1px solid #1E2D45;
    margin-bottom: 2rem;
}
.main-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.6rem;
    font-weight: 800;
    color: #F0F4FF;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin: 0;
}
.main-subtitle {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    color: #5A7A9A;
    margin-top: 0.4rem;
    font-weight: 300;
}
.accent {
    color: #3B9EFF;
}

/* KPI Cards */
.kpi-card {
    background: linear-gradient(135deg, #131E30 0%, #0F1825 100%);
    border: 1px solid #1E2D45;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #3B9EFF, #00C9A7);
}
.kpi-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #5A7A9A;
    font-weight: 500;
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-family: 'Syne', sans-serif;
    font-size: 2.1rem;
    font-weight: 700;
    color: #F0F4FF;
    line-height: 1;
}
.kpi-sub {
    font-size: 0.78rem;
    color: #4A6A8A;
    margin-top: 0.3rem;
}

/* Section headers */
.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #C8D8F0;
    letter-spacing: -0.01em;
    margin: 2rem 0 0.75rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1E2D45;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Métricas tabla */
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
}

/* Selectbox y widgets en sidebar */
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stMultiSelect > div > div {
    background-color: #1A2535 !important;
    border-color: #2A3D55 !important;
    color: #C8D8F0 !important;
    border-radius: 8px;
}

/* Pills de info */
.info-pill {
    display: inline-block;
    background: #1A2A3A;
    border: 1px solid #2A4060;
    color: #7EB8D4;
    font-size: 0.75rem;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    margin: 0.15rem;
    font-family: 'DM Sans', sans-serif;
}

/* Divider */
.custom-divider {
    border: none;
    border-top: 1px solid #1E2D45;
    margin: 1.5rem 0;
}

/* Plotly chart background override */
.js-plotly-plot .plotly .bg {
    fill: transparent !important;
}

/* Sidebar logo area */
.sidebar-brand {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 800;
    color: #F0F4FF;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
}
.sidebar-tagline {
    font-size: 0.72rem;
    color: #3B7ABF;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* Estado vacío */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #3A5A7A;
}
.empty-state-icon {
    font-size: 3.5rem;
    margin-bottom: 1rem;
}
.empty-state-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #4A7A9A;
    margin-bottom: 0.5rem;
}
.empty-state-text {
    font-size: 0.9rem;
    color: #2A4A6A;
    line-height: 1.6;
}

/* Toggle radio como botones */
div[data-testid="stRadio"] > div {
    flex-direction: row;
    gap: 0.5rem;
}
div[data-testid="stRadio"] label {
    background: #1A2535;
    border: 1px solid #2A3D55;
    border-radius: 6px;
    padding: 0.3rem 0.8rem;
    cursor: pointer;
    font-size: 0.88rem;
    font-weight: 500;
    color: #E8EDF5 !important;
    text-transform: none !important;
    letter-spacing: normal !important;
}
div[data-testid="stRadio"] label p,
div[data-testid="stRadio"] label span {
    color: #E8EDF5 !important;
    font-size: 0.88rem !important;
}
</style>
""", unsafe_allow_html=True)


# ─── Helpers de UI ────────────────────────────────────────────────────────────

def kpi_card(label: str, value: str, sub: str = "") -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {"<div class='kpi-sub'>" + sub + "</div>" if sub else ""}
    </div>
    """

def section_header(icon: str, title: str):
    st.markdown(f'<div class="section-header">{icon} {title}</div>', unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 0 1.5rem 0; border-bottom: 1px solid #1E2D45; margin-bottom: 1.5rem;">
        <div class="sidebar-brand">⚾ Pitch Analyzer</div>
        <div class="sidebar-tagline">MLB Statcast · Baseball Savant</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Búsqueda de pitcher ──
    st.markdown('<p style="color:#9BAABB;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem;">Buscar Pitcher</p>', unsafe_allow_html=True)
    pitcher_name = st.text_input(
        label="pitcher_search",
        placeholder="Ej: Gerrit Cole, Sandy Alcantara...",
        label_visibility="collapsed",
    )

    pitcher_id   = None
    pitcher_label = None

    if pitcher_name and len(pitcher_name) >= 3:
        with st.spinner("Buscando..."):
            results = search_pitcher(pitcher_name)

        if results.empty:
            st.warning("No se encontró ningún pitcher con ese nombre.")
        else:
            options = {
                f"{row['name_first']} {row['name_last']} (ID: {row['key_mlbam']})": int(row["key_mlbam"])
                for _, row in results.iterrows()
            }
            selected = st.selectbox(
                label="Seleccionar",
                options=list(options.keys()),
                label_visibility="collapsed",
            )
            pitcher_id    = options[selected]
            pitcher_label = selected.split(" (ID:")[0]

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    # ── Temporada ──
    st.markdown('<p style="color:#9BAABB;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem;">Temporada</p>', unsafe_allow_html=True)
    season = st.selectbox(
        label="season",
        options=[2024, 2023, 2022, 2021, 2020, 2019],
        label_visibility="collapsed",
    )

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    # ── Mano del bateador ──
    st.markdown('<p style="color:#9BAABB;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem;">Mano del Bateador</p>', unsafe_allow_html=True)
    batter_hand = st.radio(
        label="batter_hand",
        options=["Todos", "Zurdo (L)", "Diestro (R)"],
        label_visibility="collapsed",
        horizontal=True,
    )
    hand_filter_map = {"Todos": None, "Zurdo (L)": "L", "Diestro (R)": "R"}
    hand_filter = hand_filter_map[batter_hand]

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    # ── Filtro de pitch types (solo visible cuando hay data) ──
    pitch_filter_placeholder = st.empty()

    st.markdown("""
    <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #1A2535;">
        <p style="font-size:0.7rem; color:#2A4060; line-height:1.5;">
            Data: <a href="https://baseballsavant.mlb.com" style="color:#3B5A7A;">Baseball Savant</a><br>
            API: <a href="https://github.com/jldbc/pybaseball" style="color:#3B5A7A;">pybaseball</a>
        </p>
    </div>
    """, unsafe_allow_html=True)


# ─── Main Content ─────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="main-header">
    <div class="main-title">Pitch <span class="accent">Effectiveness</span> Analyzer</div>
    <div class="main-subtitle">Análisis cuantitativo de pitcheos MLB · Powered by Statcast</div>
</div>
""", unsafe_allow_html=True)


# ── Estado vacío (sin pitcher seleccionado) ───────────────────────────────────

if pitcher_id is None:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">⚾</div>
        <div class="empty-state-title">Busca un pitcher para comenzar</div>
        <div class="empty-state-text">
            Escribe al menos 3 letras del nombre en el panel izquierdo.<br>
            Los datos provienen de Baseball Savant (Statcast) en tiempo real.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ── Carga de datos ────────────────────────────────────────────────────────────

with st.spinner(f"Cargando datos de {pitcher_label} — Temporada {season}..."):
    raw_df = load_pitcher_data(pitcher_id, season)

validation = validate_dataframe(raw_df)

if not validation["valid"]:
    st.error(f"⚠️ {validation['message']}")
    st.stop()

# Aplicar filtro de mano del bateador si aplica
df = raw_df.copy()
if hand_filter:
    df = df[df["stand"] == hand_filter]
    if len(df) < 20:
        st.warning(f"Solo {len(df)} pitcheos contra bateadores {'zurdos' if hand_filter == 'L' else 'diestros'}. Considera usar 'Todos'.")

# ── Filtro de pitch types en sidebar (dinámico con la data cargada) ───────────
all_pitch_types = sorted(raw_df["pitch_type"].unique().tolist())
pitch_name_map  = raw_df.drop_duplicates("pitch_type").set_index("pitch_type")["pitch_name_clean"].to_dict()
pitch_options   = [f"{pt} — {pitch_name_map.get(pt, pt)}" for pt in all_pitch_types]

with pitch_filter_placeholder:
    st.markdown('<p style="color:#9BAABB;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem;">Tipos de Pitcheo</p>', unsafe_allow_html=True)
    selected_pitches_raw = st.multiselect(
        label="pitch_types",
        options=pitch_options,
        default=pitch_options,
        label_visibility="collapsed",
    )

selected_pitch_types = [p.split(" — ")[0] for p in selected_pitches_raw]
if selected_pitch_types:
    df = df[df["pitch_type"].isin(selected_pitch_types)]


# ── Calcular métricas ─────────────────────────────────────────────────────────

kpis        = get_summary_kpis(df)
metrics_df  = get_pitch_metrics(df)
dominant_df = get_dominant_pitch_per_count(df)
matchup_df  = get_matchup_metrics(df)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 — KPI Cards
# ─────────────────────────────────────────────────────────────────────────────

section_header("📊", f"{pitcher_label} · {season}")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(kpi_card(
        "Total Pitcheos",
        f"{kpis.get('total_pitches', 0):,}",
        f"{kpis.get('total_games', 0)} juegos"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(kpi_card(
        "Pitch Types",
        str(kpis.get("unique_pitch_types", 0)),
        "en su arsenal"
    ), unsafe_allow_html=True)

with col3:
    st.markdown(kpi_card(
        "Whiff Rate Global",
        f"{kpis.get('global_whiff_rate', 0)}%",
        "todos los pitcheos"
    ), unsafe_allow_html=True)

with col4:
    st.markdown(kpi_card(
        "Pitch Principal",
        kpis.get("primary_pitch", "—"),
        "más utilizado"
    ), unsafe_allow_html=True)

with col5:
    st.markdown(kpi_card(
        "Velocidad Principal",
        f"{kpis.get('primary_pitch_velo', 0)} MPH",
        "promedio pitch principal"
    ), unsafe_allow_html=True)

st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 2 — Arsenal y Velocidad
# ─────────────────────────────────────────────────────────────────────────────

section_header("🎯", "Arsenal del Pitcher")

col_left, col_right = st.columns([1.4, 1], gap="large")

with col_left:
    st.plotly_chart(
        chart_pitch_usage(metrics_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with col_right:
    st.plotly_chart(
        chart_velocity(metrics_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 — Tabla de métricas
# ─────────────────────────────────────────────────────────────────────────────

section_header("📋", "Métricas de Efectividad por Pitch Type")

display_cols = {
    "pitch_name_clean":   "Tipo de Pitcheo",
    "count":              "Lanzamientos",
    "uso_pct":            "Uso %",
    "avg_velocity":       "Vel. Prom (MPH)",
    "avg_spin_rate":      "Spin Rate (RPM)",
    "whiff_rate":         "Whiff Rate %",
    "called_strike_pct":  "Called Strike %",
    "put_away_rate":      "Put-Away Rate %",
}

if not metrics_df.empty:
    table_df = metrics_df[[c for c in display_cols if c in metrics_df.columns]].copy()
    table_df = table_df.rename(columns=display_cols)

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Uso %":             st.column_config.ProgressColumn("Uso %", min_value=0, max_value=100, format="%.1f%%"),
            "Whiff Rate %":      st.column_config.ProgressColumn("Whiff Rate %", min_value=0, max_value=60, format="%.1f%%"),
            "Put-Away Rate %":   st.column_config.ProgressColumn("Put-Away Rate %", min_value=0, max_value=100, format="%.1f%%"),
            "Called Strike %":   st.column_config.ProgressColumn("Called Strike %", min_value=0, max_value=50, format="%.1f%%"),
        },
    )

st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4 — Efectividad y Heatmap de Conteos
# ─────────────────────────────────────────────────────────────────────────────

section_header("🔥", "Efectividad y Estrategia por Conteo")

col_eff, col_heat = st.columns([1, 1], gap="large")

with col_eff:
    st.plotly_chart(
        chart_effectiveness(metrics_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with col_heat:
    st.plotly_chart(
        chart_count_heatmap(dominant_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 5 — Matchup Zurdo vs Diestro
# ─────────────────────────────────────────────────────────────────────────────

section_header("↔️", "Matchup por Mano del Bateador")

matchup_metric = st.radio(
    label="Métrica matchup",
    options=["whiff_rate", "uso_pct"],
    format_func=lambda x: "Whiff Rate %" if x == "whiff_rate" else "Uso %",
    horizontal=True,
    label_visibility="collapsed",
)

st.plotly_chart(
    chart_matchup(matchup_df, metric=matchup_metric),
    use_container_width=True,
    config={"displayModeBar": False},
)

st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 6 — Localización de Pitcheos
# ─────────────────────────────────────────────────────────────────────────────

section_header("📍", "Localización de Pitcheos en la Zona")

col_filter1, col_filter2, _ = st.columns([1, 1, 2])

with col_filter1:
    result_filter = st.selectbox(
        label="Filtrar por resultado",
        options=["all", "whiff", "strike", "hit"],
        format_func=lambda x: {
            "all":    "Todos los pitcheos",
            "whiff":  "Solo Whiffs (swing y miss)",
            "strike": "Solo Strikes (whiff + called)",
            "hit":    "Solo Hit Into Play",
        }[x],
    )

with col_filter2:
    max_pitches = st.slider(
        label="Máx. puntos a mostrar",
        min_value=100,
        max_value=min(3000, len(df)),
        value=min(1500, len(df)),
        step=100,
    )

location_df = get_location_data(df, pitch_types=selected_pitch_types or None, result_filter=result_filter)

# Limitar cantidad de puntos para rendimiento
if len(location_df) > max_pitches:
    location_df = location_df.sample(max_pitches, random_state=42)

st.plotly_chart(
    chart_pitch_location(location_df),
    use_container_width=True,
    config={"displayModeBar": True, "displaylogo": False},
)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #1A2535; text-align: center;">
    <p style="font-size: 0.72rem; color: #2A4060; font-family: 'DM Sans', sans-serif;">
        Datos: Baseball Savant (Statcast) via pybaseball · Solo temporada regular MLB ·
        Proyecto de Mentoría — Analista de Datos Béisbol
    </p>
</div>
""", unsafe_allow_html=True)