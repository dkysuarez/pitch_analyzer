"""
data_loader.py
==============
Responsabilidad: Conectarse a Baseball Savant vía pybaseball,
obtener data Statcast de un pitcher por temporada, limpiarla
y devolverla como un DataFrame listo para métricas.

Nada de lógica de negocio aquí — solo ingesta y limpieza.
"""

import pandas as pd
import streamlit as st
import pybaseball as pb

# Columnas que realmente usamos en el proyecto
# Cualquier otra columna de Statcast se descarta para aligerar el DataFrame
COLUMNS_NEEDED = [
    "game_date",
    "pitcher",
    "player_name",
    "pitch_type",       # Tipo de pitcheo: FF, SL, CH, CU, SI, FC, FS
    "pitch_name",       # Nombre legible: 4-Seam Fastball, Slider, etc.
    "release_speed",    # Velocidad en MPH
    "release_spin_rate",# Spin rate en RPM
    "plate_x",          # Coordenada horizontal en home plate
    "plate_z",          # Coordenada vertical en home plate
    "description",      # Resultado: swinging_strike, called_strike, ball, hit_into_play, etc.
    "balls",            # Balls en el conteo antes del pitcheo
    "strikes",          # Strikes en el conteo antes del pitcheo
    "stand",            # Mano del bateador: L (zurdo) o R (diestro)
    "events",           # Resultado final del at-bat si aplica (strikeout, single, etc.)
    "zone",             # Zona del strike zone (1-9 dentro, 11-14 fuera)
    "type",             # Clasificación simple: S (strike), B (ball), X (en juego)
]

# Mapeo de códigos a nombres legibles para mostrar en el dashboard
PITCH_TYPE_NAMES = {
    "FF": "4-Seam Fastball",
    "SI": "Sinker",
    "FC": "Cutter",
    "SL": "Slider",
    "CH": "Changeup",
    "CU": "Curveball",
    "FS": "Splitter",
    "ST": "Sweeper",
    "KC": "Knuckle Curve",
    "KN": "Knuckleball",
    "EP": "Eephus",
    "CS": "Slow Curve",
    "FO": "Forkball",
    "SC": "Screwball",
}


# ─── Función principal ───────────────────────────────────────────────────────

@st.cache_data(show_spinner="Cargando datos de Baseball Savant...")
def load_pitcher_data(pitcher_id: int, season: int) -> pd.DataFrame:
    """
    Descarga y limpia los datos Statcast de un pitcher para una temporada.

    Parameters
    ----------
    pitcher_id : int
        MLB ID del pitcher (e.g., 592789 para Gerrit Cole).
    season : int
        Temporada a consultar (e.g., 2023).

    Returns
    -------
    pd.DataFrame
        DataFrame limpio con solo las columnas necesarias,
        sin filas con pitch_type nulo, listo para métricas.
    """
    # Fechas de inicio y fin de temporada regular
    start_date = f"{season}-03-20"
    end_date   = f"{season}-10-05"

    # Llamada a Baseball Savant vía pybaseball
    # Devuelve una fila por cada pitcheo lanzado por este pitcher
    raw_df = pb.statcast_pitcher(
        start_dt=start_date,
        end_dt=end_date,
        player_id=pitcher_id
    )

    if raw_df is None or raw_df.empty:
        return pd.DataFrame()  # DataFrame vacío — la app manejará este caso

    # Quedarnos solo con las columnas que usamos
    existing_cols = [c for c in COLUMNS_NEEDED if c in raw_df.columns]
    df = raw_df[existing_cols].copy()

    # Limpiar filas sin tipo de pitcheo (filas de resultado, no lanzamientos reales)
    df = df[df["pitch_type"].notna() & (df["pitch_type"] != "")]

    # Convertir fecha a datetime
    df["game_date"] = pd.to_datetime(df["game_date"])

    # Normalizar mano del bateador — solo L y R, descartar ambiguos
    df = df[df["stand"].isin(["L", "R"])]

    # Columna auxiliar: ¿fue un swinging strike? (necesaria para whiff_rate)
    df["is_whiff"] = df["description"].isin([
        "swinging_strike",
        "swinging_strike_blocked",
        "foul_tip"  # foul tip con 2 strikes también se considera whiff
    ])

    # Columna auxiliar: ¿fue un swing? (para calcular whiff_rate correctamente)
    df["is_swing"] = df["description"].isin([
        "swinging_strike",
        "swinging_strike_blocked",
        "foul",
        "foul_tip",
        "hit_into_play",
        "hit_into_play_no_out",
        "hit_into_play_score",
        "foul_bunt",
        "missed_bunt"
    ])

    # Columna auxiliar: ¿fue un called strike?
    df["is_called_strike"] = df["description"] == "called_strike"

    # Columna legible del tipo de pitcheo para gráficos
    df["pitch_name_clean"] = df["pitch_type"].map(PITCH_TYPE_NAMES).fillna(df["pitch_type"])

    return df


# ─── Búsqueda de pitcher por nombre ──────────────────────────────────────────

@st.cache_data(show_spinner="Buscando pitcher...")
def search_pitcher(name: str) -> pd.DataFrame:
    """
    Busca un pitcher por nombre en el registro de pybaseball.

    Parameters
    ----------
    name : str
        Nombre completo o parcial del pitcher (e.g., "Gerrit Cole").

    Returns
    -------
    pd.DataFrame
        DataFrame con columnas: name_first, name_last, key_mlbam (MLB ID), mlb_played_last.
        Filtra solo pitchers con actividad desde 2015 (era Statcast).
    """
    results = pb.playerid_lookup(
        last=name.split()[-1],
        first=name.split()[0] if len(name.split()) > 1 else ""
    )

    if results is None or results.empty:
        return pd.DataFrame()

    # Quedarnos solo con campos relevantes
    cols = ["name_first", "name_last", "key_mlbam", "mlb_played_last"]
    existing = [c for c in cols if c in results.columns]
    results = results[existing].copy()

    # Filtrar solo jugadores activos en era Statcast (desde 2015)
    if "mlb_played_last" in results.columns:
        results = results[results["mlb_played_last"] >= 2015]

    return results.reset_index(drop=True)


# ─── Utilidades de validación ─────────────────────────────────────────────────

def validate_dataframe(df: pd.DataFrame) -> dict:
    """
    Valida que el DataFrame tenga lo mínimo necesario para calcular métricas.

    Returns
    -------
    dict con claves:
        - valid (bool): True si el DataFrame es usable
        - message (str): Descripción del problema si no es válido
        - pitch_count (int): Total de pitcheos en el DataFrame
    """
    if df is None or df.empty:
        return {"valid": False, "message": "No se encontraron datos para este pitcher y temporada.", "pitch_count": 0}

    if "pitch_type" not in df.columns:
        return {"valid": False, "message": "El DataFrame no contiene la columna pitch_type.", "pitch_count": 0}

    pitch_count = len(df)
    if pitch_count < 50:
        return {"valid": False, "message": f"Solo {pitch_count} pitcheos encontrados. Mínimo 50 para análisis confiable.", "pitch_count": pitch_count}

    return {"valid": True, "message": "OK", "pitch_count": pitch_count}