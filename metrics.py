"""
metrics.py
==========
PROPÓSITO GENERAL DE ESTE ARCHIVO:
Este es el ENCARGADO DE CALCULAR MÉTRICAS. Su misión es:
1. Recibir el DataFrame limpio de data_loader.py (que tiene UNA FILA POR CADA LANZAMIENTO)
2. Hacer operaciones de agregación (agrupar, sumar, promediar)
3. Calcular porcentajes y estadísticas
4. Devolver DataFrames RESUMEN (una fila por tipo de lanzamiento, por conteo, etc.)

IMPORTANTE PARA EL APRENDIZ:
- Este archivo NO SABE hacer gráficos (eso es trabajo de charts.py)
- Este archivo NO SABE descargar datos (eso es trabajo de data_loader.py)
- Este archivo SOLO SABE hacer MATEMÁTICAS con los datos que le pasan

Es como el "cocinero" que toma los ingredientes (datos crudos) y los convierte
en platos preparados (métricas) para que el mesero (charts.py) los sirva bonitos.
"""

# ==============================================
# PASO 1: IMPORTAR LAS LIBRERÍAS QUE NECESITAMOS
# ==============================================
import pandas as pd
import numpy as np
# ¿Qué es numpy? Es una librería para operaciones matemáticas avanzadas.
# Aquí lo usamos principalmente para manejar valores nulos (NaN = Not a Number).
# Cuando dividimos por cero, numpy nos ayuda a poner NaN en lugar de que el programa explote.


# ==============================================
# PASO 2: FUNCIÓN PRINCIPAL - MÉTRICAS POR TIPO DE PITCHEO
# ==============================================
# Esta es la función MÁS IMPORTANTE de este archivo.
# Toma todos los lanzamientos y calcula métricas AGRUPADAS POR TIPO DE LANZAMIENTO.
# Ejemplo: ¿Cómo le fue a la recta? ¿Cómo le fue al slider?

def get_pitch_metrics(df: pd.DataFrame) -> pd.DataFrame:
    # df: pd.DataFrame → El DataFrame con todos los lanzamientos (una fila por lanzamiento)
    # -> pd.DataFrame → Devuelve un DataFrame RESUMEN (una fila por tipo de lanzamiento)

    """
    Calcula las métricas principales de efectividad por tipo de pitcheo.

    ARGUMENTOS:
    -----------
    df : pd.DataFrame
        DataFrame limpio proveniente de data_loader.load_pitcher_data()
        Debe tener columnas como: pitch_type, pitch_name_clean, release_speed,
        is_swing, is_whiff, is_called_strike, etc.

    RETORNA:
    --------
    pd.DataFrame
        Una fila por cada tipo de lanzamiento (FF, SL, CH, etc.)
        Con métricas como: uso_pct, avg_velocity, whiff_rate, etc.
    """

    # ------------------------------------------
    # PASO 2.1: VERIFICAR SI HAY DATOS
    # ------------------------------------------
    if df.empty:
        # Si el DataFrame está vacío, devolvemos un DataFrame vacío
        # Esto es importante para que el programa no falle
        return pd.DataFrame()

    # ------------------------------------------
    # PASO 2.2: CALCULAR EL TOTAL DE PITCHEOS
    # ------------------------------------------
    total_pitches = len(df)
    # len(df) = número de filas = número total de lanzamientos
    # Este número lo vamos a usar para calcular porcentajes de uso

    # ------------------------------------------
    # PASO 2.3: AGRUPAR POR TIPO DE LANZAMIENTO
    # ------------------------------------------
    # groupby es UNA DE LAS FUNCIONES MÁS IMPORTANTES de pandas
    # Significa: "Agrupa todas las filas que tengan el mismo pitch_type y pitch_name_clean"
    #
    # Ejemplo: Si tenemos 1000 lanzamientos de recta (FF) y 500 sliders (SL),
    # groupby va a crear DOS grupos: uno con las 1000 filas de FF y otro con las 500 de SL.
    # Luego podemos aplicar operaciones a CADA GRUPO por separado.

    grouped = df.groupby(["pitch_type", "pitch_name_clean"])
    # El resultado es un objeto "GroupBy" que todavía no hace nada,
    # pero está listo para que le digamos qué queremos calcular.

    # ------------------------------------------
    # PASO 2.4: CALCULAR ESTADÍSTICAS BÁSICAS POR GRUPO
    # ------------------------------------------
    # .agg() significa "aggregate" (agregar). Le decimos: para cada grupo, calcula:
    # - count: cuántas filas hay (número de lanzamientos de este tipo)
    # - mean: el promedio de release_speed (velocidad promedio)
    # - mean: el promedio de release_spin_rate (efecto promedio)
    # - sum: la suma de is_swing (total de swings a este lanzamiento)
    # - sum: la suma de is_whiff (total de whiffs a este lanzamiento)
    # - sum: la suma de is_called_strike (total de strikes cantados)

    metrics = grouped.agg(
        count=("pitch_type", "count"),                # Número de lanzamientos
        avg_velocity=("release_speed", "mean"),       # Velocidad promedio
        avg_spin_rate=("release_spin_rate", "mean"),  # Efecto promedio
        total_swings=("is_swing", "sum"),             # Total de swings
        total_whiffs=("is_whiff", "sum"),             # Total de swings fallidos
        total_called_strikes=("is_called_strike", "sum"),  # Total de strikes cantados
    ).reset_index()
    # .reset_index() es importante: convierte el índice (pitch_type, pitch_name_clean)
    # en columnas normales. Así tenemos un DataFrame plano y fácil de usar.

    # 🎯 EXPLICACIÓN DE LA SINTAXIS:
    # count=("pitch_type", "count") significa:
    # "Crea una columna llamada 'count' que sea el resultado de aplicar la función
    # 'count' a la columna 'pitch_type' de cada grupo"
    #
    # Es como decir: "Para cada grupo, cuéntame cuántas filas tienes"

    # ------------------------------------------
    # PASO 2.5: CALCULAR PORCENTAJE DE USO
    # ------------------------------------------
    # Uso % = (lanzamientos de este tipo) / (total de lanzamientos) * 100
    metrics["uso_pct"] = (metrics["count"] / total_pitches * 100).round(1)
    # .round(1) redondea a 1 decimal (23.456 → 23.5)

    # ------------------------------------------
    # PASO 2.6: CALCULAR WHIFF RATE
    # ------------------------------------------
    # Whiff Rate % = (swings fallidos) / (swings totales) * 100
    # ¡CUIDADO! Si total_swings = 0, la división daría error.
    # Por eso usamos .replace(0, np.nan): si total_swings es 0, lo reemplazamos por NaN
    # NaN = Not a Number. Cuando pandas ve NaN, no hace la división.

    metrics["whiff_rate"] = (
        metrics["total_whiffs"] / metrics["total_swings"].replace(0, np.nan) * 100
    ).round(1)

    # ------------------------------------------
    # PASO 2.7: CALCULAR CALLED STRIKE %
    # ------------------------------------------
    # Called Strike % = (strikes cantados) / (total lanzamientos de este tipo) * 100
    metrics["called_strike_pct"] = (
        metrics["total_called_strikes"] / metrics["count"] * 100
    ).round(1)

    # ------------------------------------------
    # PASO 2.8: REDONDEAR VELOCIDAD Y SPIN
    # ------------------------------------------
    metrics["avg_velocity"] = metrics["avg_velocity"].round(1)
    metrics["avg_spin_rate"] = metrics["avg_spin_rate"].round(0).astype("Int64")
    # .astype("Int64") convierte a número entero (sin decimales)
    # El spin rate normalmente no tiene decimales

    # ------------------------------------------
    # PASO 2.9: CALCULAR PUT-AWAY RATE (OPCIONAL - AVANZADO)
    # ------------------------------------------
    # Put-away rate = % de lanzamientos con 2 strikes que terminan en ponche
    # Es una métrica más avanzada que mide "capacidad de definir el turno"

    # Filtrar SOLO los lanzamientos con 2 strikes
    two_strike_df = df[df["strikes"] == 2].copy()

    if not two_strike_df.empty:
        # Crear columna auxiliar: ¿este lanzamiento fue un ponche?
        two_strike_df["is_putaway"] = two_strike_df["events"] == "strikeout"
        # events = "strikeout" significa que el turno terminó en ponche

        # Agrupar por tipo de lanzamiento
        putaway = two_strike_df.groupby("pitch_type").agg(
            two_strike_count=("pitch_type", "count"),  # Lanzamientos con 2 strikes de este tipo
            putaways=("is_putaway", "sum")             # Cuántos de esos fueron ponches
        ).reset_index()

        # Calcular put-away rate
        putaway["put_away_rate"] = (
            putaway["putaways"] / putaway["two_strike_count"] * 100
        ).round(1)

        # Combinar con metrics (como un "VLOOKUP" de Excel)
        metrics = metrics.merge(
            putaway[["pitch_type", "put_away_rate", "two_strike_count"]],
            on="pitch_type",
            how="left"
        )
        # left join: mantiene todas las filas de metrics y añade las de putaway
    else:
        # Si no hay lanzamientos con 2 strikes, poner NaN
        metrics["put_away_rate"] = np.nan
        metrics["two_strike_count"] = 0

    # ------------------------------------------
    # PASO 2.10: ORDENAR POR USO (DE MÁS A MENOS)
    # ------------------------------------------
    metrics = metrics.sort_values("uso_pct", ascending=False).reset_index(drop=True)
    # ascending=False → orden descendente (mayor a menor)
    # reset_index(drop=True) → reinicia el índice (0,1,2,3...)

    # ------------------------------------------
    # PASO 2.11: SELECCIONAR COLUMNAS FINALES
    # ------------------------------------------
    final_cols = [
        "pitch_type",           # Código (FF, SL)
        "pitch_name_clean",     # Nombre bonito (4-Seam Fastball)
        "count",                # Número de lanzamientos
        "uso_pct",              # % de uso
        "avg_velocity",         # Velocidad promedio
        "avg_spin_rate",        # Efecto promedio
        "whiff_rate",           #% Swings fallidos
        "called_strike_pct",    #% Strikes cantados
        "put_away_rate",        #% Ponches con 2 strikes
        "two_strike_count",     # Lanzamientos con 2 strikes (para referencia)
    ]

    # Devolver solo las columnas que existen (por si alguna falta)
    return metrics[[c for c in final_cols if c in metrics.columns]]


# ==============================================
# PASO 3: FUNCIÓN PARA DISTRIBUCIÓN POR CONTEO
# ==============================================
# ¿Qué lanza este pitcher en cada situación (0-0, 3-2, etc.)?

def get_count_distribution(df: pd.DataFrame) -> pd.DataFrame:
    # df: pd.DataFrame → Todos los lanzamientos
    # -> pd.DataFrame → Una fila por (balls, strikes, pitch_type)

    """
    Calcula qué tipo de lanzamiento se usó en cada combinación de bolas y strikes.

    ARGUMENTOS:
    -----------
    df : pd.DataFrame
        Todos los lanzamientos

    RETORNA:
    --------
    pd.DataFrame
        Columnas: balls, strikes, pitch_type, pitch_name_clean, count, pct_in_count
        pct_in_count = % de veces que se usó este pitch en este conteo específico
    """

    if df.empty:
        return pd.DataFrame()

    # ------------------------------------------
    # PASO 3.1: AGRUPAR POR CONTEO Y TIPO DE PITCH
    # ------------------------------------------
    # Agrupamos por: balls, strikes, pitch_type, pitch_name_clean
    # Queremos saber, para cada conteo (ej: 3 bolas, 2 strikes),
    # cuántos lanzamientos de cada tipo se hicieron.

    count_df = df.groupby(["balls", "strikes", "pitch_type", "pitch_name_clean"]).agg(
        count=("pitch_type", "count")  # Número de lanzamientos en este grupo
    ).reset_index()

    # ------------------------------------------
    # PASO 3.2: CALCULAR TOTAL POR CONTEO
    # ------------------------------------------
    # Para saber el porcentaje dentro de cada conteo, necesitamos
    # el total de lanzamientos en ESE conteo específico.

    total_per_count = df.groupby(["balls", "strikes"]).size().reset_index(name="total_in_count")
    # .size() cuenta cuántas filas hay en cada grupo
    # El resultado es: para (balls=0, strikes=0) hay X lanzamientos, etc.

    # ------------------------------------------
    # PASO 3.3: COMBINAR (JOIN) LOS DATAFRAMES
    # ------------------------------------------
    # Como en Excel: BUSCARV para añadir total_in_count a count_df
    count_df = count_df.merge(total_per_count, on=["balls", "strikes"], how="left")

    # ------------------------------------------
    # PASO 3.4: CALCULAR PORCENTAJE DENTRO DEL CONTEO
    # ------------------------------------------
    count_df["pct_in_count"] = (count_df["count"] / count_df["total_in_count"] * 100).round(1)

    # ------------------------------------------
    # PASO 3.5: ORDENAR
    # ------------------------------------------
    return count_df.sort_values(["balls", "strikes", "pct_in_count"],
                                ascending=[True, True, False])


# ==============================================
# PASO 4: FUNCIÓN PARA PITCH DOMINANTE POR CONTEO
# ==============================================
# Versión simplificada: solo el lanzamiento MÁS usado en cada conteo

def get_dominant_pitch_per_count(df: pd.DataFrame) -> pd.DataFrame:
    # df: pd.DataFrame → Todos los lanzamientos
    # -> pd.DataFrame → Una fila por conteo, con el pitch dominante

    """
    Devuelve el tipo de lanzamiento más usado en cada conteo.
    Útil para el heatmap del dashboard.

    ARGUMENTOS:
    -----------
    df : pd.DataFrame
        Todos los lanzamientos

    RETORNA:
    --------
    pd.DataFrame
        Una fila por conteo (balls, strikes) con:
        - pitch_type: el más usado
        - pitch_name_clean: nombre bonito
        - pct_in_count: % de uso en ese conteo
    """

    # ------------------------------------------
    # PASO 4.1: OBTENER DISTRIBUCIÓN COMPLETA
    # ------------------------------------------
    count_dist = get_count_distribution(df)
    if count_dist.empty:
        return pd.DataFrame()

    # ------------------------------------------
    # PASO 4.2: QUEDARSE CON EL PRIMERO (MAYOR %) DE CADA CONTEO
    # ------------------------------------------
    # 1. Ordenar por pct_in_count descendente (mayor a menor)
    # 2. Agrupar por (balls, strikes)
    # 3. .first() → tomar la primera fila de cada grupo (la de mayor %)

    dominant = (
        count_dist
        .sort_values("pct_in_count", ascending=False)
        .groupby(["balls", "strikes"])
        .first()
        .reset_index()
    )

    return dominant


# ==============================================
# PASO 5: FUNCIÓN PARA MATCHUP POR MANO DEL BATEADOR
# ==============================================
# ¿Cómo le va a este pitcher contra zurdos vs diestros?

def get_matchup_metrics(df: pd.DataFrame) -> pd.DataFrame:
    # df: pd.DataFrame → Todos los lanzamientos
    # -> pd.DataFrame → Una fila por (pitch_type, stand)

    """
    Calcula métricas separadas por mano del bateador.

    ARGUMENTOS:
    -----------
    df : pd.DataFrame
        Todos los lanzamientos

    RETORNA:
    --------
    pd.DataFrame
        Columnas: pitch_type, pitch_name_clean, stand (L/R),
        uso_pct, whiff_rate, count, avg_velocity
    """

    if df.empty:
        return pd.DataFrame()

    # ------------------------------------------
    # PASO 5.1: CALCULAR TOTALES POR MANO
    # ------------------------------------------
    # Necesitamos estos totales para calcular porcentajes de uso
    total_vs_left = len(df[df["stand"] == "L"])    # Lanzamientos vs zurdos
    total_vs_right = len(df[df["stand"] == "R"])   # Lanzamientos vs diestros

    # ------------------------------------------
    # PASO 5.2: AGRUPAR POR PITCH TYPE Y MANO
    # ------------------------------------------
    matchup = df.groupby(["pitch_type", "pitch_name_clean", "stand"]).agg(
        count=("pitch_type", "count"),              # Lanzamientos de este tipo vs esta mano
        total_swings=("is_swing", "sum"),           # Swings a este pitch vs esta mano
        total_whiffs=("is_whiff", "sum"),           # Whiffs a este pitch vs esta mano
        avg_velocity=("release_speed", "mean"),     # Velocidad promedio
    ).reset_index()

    # ------------------------------------------
    # PASO 5.3: CALCULAR PORCENTAJE DE USO POR MANO
    # ------------------------------------------
    # .apply() con lambda: aplica una función personalizada a cada fila
    matchup["uso_pct"] = matchup.apply(
        lambda row: round(
            row["count"] / (total_vs_left if row["stand"] == "L" else total_vs_right) * 100, 1
        ), axis=1
    )
    # axis=1 significa "aplicar a cada fila" (axis=0 sería a cada columna)

    # 🎯 EXPLICACIÓN DE LA LAMBDA:
    # Esta función anónima (sin nombre) recibe una fila (row)
    # Si row["stand"] es "L", divide entre total_vs_left, si no, entre total_vs_right
    # Luego multiplica por 100 y redondea a 1 decimal

    # ------------------------------------------
    # PASO 5.4: CALCULAR WHIFF RATE POR MANO
    # ------------------------------------------
    matchup["whiff_rate"] = (
        matchup["total_whiffs"] / matchup["total_swings"].replace(0, np.nan) * 100
    ).round(1)

    # ------------------------------------------
    # PASO 5.5: REDONDEAR VELOCIDAD
    # ------------------------------------------
    matchup["avg_velocity"] = matchup["avg_velocity"].round(1)

    # ------------------------------------------
    # PASO 5.6: ORDENAR
    # ------------------------------------------
    return matchup.sort_values(["pitch_type", "stand"]).reset_index(drop=True)


# ==============================================
# PASO 6: FUNCIÓN PARA DATOS DE LOCALIZACIÓN
# ==============================================
# Prepara los datos para el scatter plot de la zona de strike

def get_location_data(df: pd.DataFrame, pitch_types: list = None, result_filter: str = "all") -> pd.DataFrame:
    # df: pd.DataFrame → Todos los lanzamientos
    # pitch_types: list → Filtrar por estos tipos de lanzamiento (None = todos)
    # result_filter: str → Tipo de resultado a incluir
    # -> pd.DataFrame → Datos listos para el gráfico de dispersión

    """
    Filtra y prepara los datos de ubicación (plate_x, plate_z) para el scatter plot.

    ARGUMENTOS:
    -----------
    df : pd.DataFrame
        Todos los lanzamientos
    pitch_types : list, opcional
        Lista de códigos de lanzamiento a incluir. None = todos.
    result_filter : str
        "all"    : todos los lanzamientos
        "whiff"  : solo swings fallidos
        "strike" : strikes (cantados + fallidos)
        "hit"    : solo lanzamientos en juego (hit)

    RETORNA:
    --------
    pd.DataFrame
        Columnas: plate_x, plate_z, pitch_type, pitch_name_clean, description, stand
    """

    if df.empty:
        return pd.DataFrame()

    # ------------------------------------------
    # PASO 6.1: COPIAR PARA NO MODIFICAR ORIGINAL
    # ------------------------------------------
    filtered = df.copy()

    # ------------------------------------------
    # PASO 6.2: APLICAR FILTRO DE TIPOS DE PITCH
    # ------------------------------------------
    if pitch_types:
        # Si nos pasaron una lista de tipos, filtrar por esos
        filtered = filtered[filtered["pitch_type"].isin(pitch_types)]

    # ------------------------------------------
    # PASO 6.3: APLICAR FILTRO POR RESULTADO
    # ------------------------------------------
    # Diccionario que mapea el filtro a los valores de description
    result_map = {
        "whiff":  ["swinging_strike", "swinging_strike_blocked", "foul_tip"],
        "strike": ["swinging_strike", "swinging_strike_blocked", "called_strike", "foul_tip"],
        "hit":    ["hit_into_play", "hit_into_play_no_out", "hit_into_play_score"],
    }

    if result_filter in result_map:
        filtered = filtered[filtered["description"].isin(result_map[result_filter])]

    # ------------------------------------------
    # PASO 6.4: ELIMINAR FILAS SIN COORDENADAS
    # ------------------------------------------
    # Para dibujar puntos necesitamos X e Y. Si faltan, no sirven.
    filtered = filtered.dropna(subset=["plate_x", "plate_z"])

    # ------------------------------------------
    # PASO 6.5: SELECCIONAR SOLO COLUMNAS NECESARIAS
    # ------------------------------------------
    return filtered[["plate_x", "plate_z", "pitch_type", "pitch_name_clean", "description", "stand"]].reset_index(drop=True)


# ==============================================
# PASO 7: FUNCIÓN PARA KPIS GLOBALES
# ==============================================
# Resumen general del pitcher (para las tarjetas de arriba del dashboard)

def get_summary_kpis(df: pd.DataFrame) -> dict:
    # df: pd.DataFrame → Todos los lanzamientos
    # -> dict → Diccionario con los KPIs

    """
    Calcula los KPIs de resumen general del pitcher.

    ARGUMENTOS:
    -----------
    df : pd.DataFrame
        Todos los lanzamientos

    RETORNA:
    --------
    dict
        Diccionario con:
        - total_pitches: número total de lanzamientos
        - unique_pitch_types: cuántos tipos diferentes usa
        - global_whiff_rate: % de swings fallidos (todos los lanzamientos)
        - primary_pitch: nombre del lanzamiento más usado
        - primary_pitch_velo: velocidad de ese lanzamiento
        - total_games: en cuántos juegos participó
    """

    if df.empty:
        return {}

    # ------------------------------------------
    # PASO 7.1: MÉTRICAS BÁSICAS
    # ------------------------------------------
    total_swings = df["is_swing"].sum()      # Total de swings (todos los lanzamientos)
    total_whiffs = df["is_whiff"].sum()      # Total de swings fallidos

    # ------------------------------------------
    # PASO 7.2: PITCH PRINCIPAL
    # ------------------------------------------
    # .value_counts() cuenta cuántas veces aparece cada pitch_type
    # .idxmax() devuelve el índice (pitch_type) del valor máximo
    primary_pitch_type = df["pitch_type"].value_counts().idxmax()

    # Buscar el nombre bonito de ese pitch_type
    primary_pitch_name = df.loc[df["pitch_type"] == primary_pitch_type, "pitch_name_clean"].iloc[0]

    # Velocidad promedio de ese pitch
    primary_velo = df.loc[df["pitch_type"] == primary_pitch_type, "release_speed"].mean()

    # ------------------------------------------
    # PASO 7.3: CALCULAR JUEGOS ÚNICOS
    # ------------------------------------------
    # .nunique() cuenta valores únicos
    # .dt.date extrae solo la fecha (sin hora)
    if "game_date" in df.columns:
        total_games = df["game_date"].dt.date.nunique()
    else:
        total_games = 0

    # ------------------------------------------
    # PASO 7.4: ARMAR DICCIONARIO CON RESULTADOS
    # ------------------------------------------
    return {
        "total_pitches":      int(len(df)),
        "unique_pitch_types": int(df["pitch_type"].nunique()),
        "global_whiff_rate":  round(total_whiffs / total_swings * 100, 1) if total_swings > 0 else 0.0,
        "primary_pitch":      primary_pitch_name,
        "primary_pitch_velo": round(primary_velo, 1) if not pd.isna(primary_velo) else 0.0,
        "total_games":        total_games,
    }


# ==============================================
# NOTA FINAL: ¿POR QUÉ DEVOLVEMOS DATAFRAMES Y DICCIONARIOS?
# ==============================================
# - DataFrames: cuando tenemos TABLAS de datos (varias filas, varias columnas)
#   Ejemplo: métricas por tipo de lanzamiento, matchup por mano
#
# - Diccionarios: cuando tenemos VALORES SUELTOS que no forman una tabla
#   Ejemplo: KPIs globales (total_pitches, primary_pitch, etc.)
#
# Esta consistencia hace que charts.py y app.py sepan QUÉ esperar de cada función.