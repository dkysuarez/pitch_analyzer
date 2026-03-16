"""
metrics.py
==========
GENERAL PURPOSE OF THIS FILE:
This file is responsible for CALCULATING METRICS. Its mission is:
1. Receive the clean DataFrame from data_loader.py (which has ONE ROW PER PITCH)
2. Perform aggregation operations (grouping, summing, averaging)
3. Calculate percentages and statistics
4. Return SUMMARY DataFrames (one row per pitch type, per count, etc.)

IMPORTANT FOR THE LEARNER:
- This file does NOT know how to make charts (that is charts.py's job)
- This file does NOT know how to download data (that is data_loader.py's job)
- This file ONLY knows how to do MATH with the data it receives

Think of it as the "chef" who takes raw ingredients (data) and converts them
into prepared dishes (metrics) for the waiter (charts.py) to serve nicely.
"""

# ==============================================
# STEP 1: IMPORT THE LIBRARIES WE NEED
# ==============================================
import pandas as pd
import numpy as np
# What is numpy? It is a library for advanced mathematical operations.
# Here we use it mainly to handle null values (NaN = Not a Number).
# When we divide by zero, numpy helps us put NaN instead of crashing the program.


# ==============================================
# STEP 2: MAIN FUNCTION — METRICS BY PITCH TYPE
# ==============================================
# This is the MOST IMPORTANT function in this file.
# It takes all pitches and calculates metrics GROUPED BY PITCH TYPE.
# Example: How did the fastball perform? How did the slider perform?

def get_pitch_metrics(df: pd.DataFrame) -> pd.DataFrame:
    # df: pd.DataFrame → DataFrame with all pitches (one row per pitch)
    # -> pd.DataFrame → Returns a SUMMARY DataFrame (one row per pitch type)

    """
    Calculates the main effectiveness metrics by pitch type.

    PARAMETERS:
    -----------
    df : pd.DataFrame
        Clean DataFrame from data_loader.load_pitcher_data()
        Must have columns like: pitch_type, pitch_name_clean, release_speed,
        is_swing, is_whiff, is_called_strike, etc.

    RETURNS:
    --------
    pd.DataFrame
        One row per pitch type (FF, SL, CH, etc.)
        With metrics like: uso_pct, avg_velocity, whiff_rate, etc.
    """

    # ------------------------------------------
    # STEP 2.1: CHECK IF THERE IS DATA
    # ------------------------------------------
    if df.empty:
        # If the DataFrame is empty, return an empty DataFrame.
        # This is important so the program does not crash.
        return pd.DataFrame()

    # ------------------------------------------
    # STEP 2.2: CALCULATE TOTAL PITCH COUNT
    # ------------------------------------------
    total_pitches = len(df)
    # len(df) = number of rows = total number of pitches thrown.
    # We use this number to calculate usage percentages.

    # ------------------------------------------
    # STEP 2.3: GROUP BY PITCH TYPE
    # ------------------------------------------
    # groupby is ONE OF THE MOST IMPORTANT functions in pandas.
    # It means: "Group all rows that have the same pitch_type and pitch_name_clean."
    #
    # Example: If we have 1000 fastballs (FF) and 500 sliders (SL),
    # groupby creates TWO groups: one with the 1000 FF rows and one with the 500 SL rows.
    # We can then apply operations to EACH GROUP separately.

    grouped = df.groupby(["pitch_type", "pitch_name_clean"])
    # The result is a "GroupBy" object that does nothing yet,
    # but is ready for us to tell it what we want to calculate.

    # ------------------------------------------
    # STEP 2.4: CALCULATE BASIC STATISTICS PER GROUP
    # ------------------------------------------
    # .agg() means "aggregate". We tell it: for each group, calculate:
    # - count: how many rows there are (number of pitches of this type)
    # - mean: average release_speed (average velocity)
    # - mean: average release_spin_rate (average spin)
    # - sum: sum of is_swing (total swings at this pitch)
    # - sum: sum of is_whiff (total whiffs at this pitch)
    # - sum: sum of is_called_strike (total called strikes)

    metrics = grouped.agg(
        count=("pitch_type", "count"),                # Number of pitches
        avg_velocity=("release_speed", "mean"),       # Average velocity
        avg_spin_rate=("release_spin_rate", "mean"),  # Average spin rate
        total_swings=("is_swing", "sum"),             # Total swings
        total_whiffs=("is_whiff", "sum"),             # Total missed swings
        total_called_strikes=("is_called_strike", "sum"),  # Total called strikes
    ).reset_index()
    # .reset_index() is important: it converts the index (pitch_type, pitch_name_clean)
    # into regular columns, giving us a flat, easy-to-use DataFrame.

    # SYNTAX EXPLANATION:
    # count=("pitch_type", "count") means:
    # "Create a column called 'count' that is the result of applying the 'count'
    # function to the 'pitch_type' column of each group."
    # It is like saying: "For each group, count how many rows you have."

    # ------------------------------------------
    # STEP 2.5: CALCULATE USAGE PERCENTAGE
    # ------------------------------------------
    # Usage % = (pitches of this type) / (total pitches) * 100
    metrics["uso_pct"] = (metrics["count"] / total_pitches * 100).round(1)
    # .round(1) rounds to 1 decimal place (23.456 → 23.5)

    # ------------------------------------------
    # STEP 2.6: CALCULATE WHIFF RATE
    # ------------------------------------------
    # Whiff Rate % = (missed swings) / (total swings) * 100
    # CAUTION! If total_swings = 0, the division would cause an error.
    # That is why we use .replace(0, np.nan): if total_swings is 0,
    # we replace it with NaN. When pandas sees NaN, it skips the division.

    metrics["whiff_rate"] = (
        metrics["total_whiffs"] / metrics["total_swings"].replace(0, np.nan) * 100
    ).round(1)

    # ------------------------------------------
    # STEP 2.7: CALCULATE CALLED STRIKE %
    # ------------------------------------------
    # Called Strike % = (called strikes) / (total pitches of this type) * 100
    metrics["called_strike_pct"] = (
        metrics["total_called_strikes"] / metrics["count"] * 100
    ).round(1)

    # ------------------------------------------
    # STEP 2.8: ROUND VELOCITY AND SPIN
    # ------------------------------------------
    metrics["avg_velocity"] = metrics["avg_velocity"].round(1)
    metrics["avg_spin_rate"] = metrics["avg_spin_rate"].round(0).astype("Int64")
    # .astype("Int64") converts to integer (no decimals).
    # Spin rate is typically reported without decimals.

    # ------------------------------------------
    # STEP 2.9: CALCULATE PUT-AWAY RATE (ADVANCED)
    # ------------------------------------------
    # Put-away rate = % of pitches with 2 strikes that end in a strikeout.
    # It is a more advanced metric measuring "ability to close out an at-bat."

    # Filter ONLY pitches thrown with 2 strikes
    two_strike_df = df[df["strikes"] == 2].copy()

    if not two_strike_df.empty:
        # Helper column: did this pitch result in a strikeout?
        two_strike_df["is_putaway"] = two_strike_df["events"] == "strikeout"
        # events == "strikeout" means the at-bat ended in a strikeout.

        # Group by pitch type
        putaway = two_strike_df.groupby("pitch_type").agg(
            two_strike_count=("pitch_type", "count"),  # 2-strike pitches of this type
            putaways=("is_putaway", "sum")             # How many of those were strikeouts
        ).reset_index()

        # Calculate put-away rate
        putaway["put_away_rate"] = (
            putaway["putaways"] / putaway["two_strike_count"] * 100
        ).round(1)

        # Merge with metrics (like a VLOOKUP in Excel)
        metrics = metrics.merge(
            putaway[["pitch_type", "put_away_rate", "two_strike_count"]],
            on="pitch_type",
            how="left"
        )
        # left join: keeps all rows from metrics and adds the putaway columns
    else:
        # If there are no 2-strike pitches, set NaN
        metrics["put_away_rate"] = np.nan
        metrics["two_strike_count"] = 0

    # ------------------------------------------
    # STEP 2.10: SORT BY USAGE (HIGH TO LOW)
    # ------------------------------------------
    metrics = metrics.sort_values("uso_pct", ascending=False).reset_index(drop=True)
    # ascending=False → descending order (highest to lowest)
    # reset_index(drop=True) → resets the index (0, 1, 2, 3...)

    # ------------------------------------------
    # STEP 2.11: SELECT FINAL COLUMNS
    # ------------------------------------------
    final_cols = [
        "pitch_type",           # Code (FF, SL)
        "pitch_name_clean",     # Human-readable name (4-Seam Fastball)
        "count",                # Number of pitches
        "uso_pct",              # Usage %
        "avg_velocity",         # Average velocity
        "avg_spin_rate",        # Average spin rate
        "whiff_rate",           # Missed swing %
        "called_strike_pct",    # Called strike %
        "put_away_rate",        # Strikeout % with 2 strikes
        "two_strike_count",     # 2-strike pitches (for reference)
    ]

    # Return only the columns that exist (in case any is missing)
    return metrics[[c for c in final_cols if c in metrics.columns]]


# ==============================================
# STEP 3: COUNT DISTRIBUTION FUNCTION
# ==============================================
# What does this pitcher throw in each situation (0-0, 3-2, etc.)?

def get_count_distribution(df: pd.DataFrame) -> pd.DataFrame:
    # df: pd.DataFrame → All pitches
    # -> pd.DataFrame → One row per (balls, strikes, pitch_type)

    """
    Calculates which pitch type was used in each balls-strikes count combination.

    PARAMETERS:
    -----------
    df : pd.DataFrame
        All pitches

    RETURNS:
    --------
    pd.DataFrame
        Columns: balls, strikes, pitch_type, pitch_name_clean, count, pct_in_count
        pct_in_count = % of times this pitch was used in this specific count
    """

    if df.empty:
        return pd.DataFrame()

    # ------------------------------------------
    # STEP 3.1: GROUP BY COUNT AND PITCH TYPE
    # ------------------------------------------
    # We group by: balls, strikes, pitch_type, pitch_name_clean.
    # We want to know, for each count (e.g., 3 balls, 2 strikes),
    # how many pitches of each type were thrown.

    count_df = df.groupby(["balls", "strikes", "pitch_type", "pitch_name_clean"]).agg(
        count=("pitch_type", "count")  # Number of pitches in this group
    ).reset_index()

    # ------------------------------------------
    # STEP 3.2: CALCULATE TOTAL PER COUNT
    # ------------------------------------------
    # To compute the percentage within each count, we need
    # the total number of pitches in THAT specific count.

    total_per_count = df.groupby(["balls", "strikes"]).size().reset_index(name="total_in_count")
    # .size() counts how many rows are in each group.
    # Result: for (balls=0, strikes=0) there are X pitches, etc.

    # ------------------------------------------
    # STEP 3.3: MERGE THE DATAFRAMES
    # ------------------------------------------
    # Like a VLOOKUP in Excel: add total_in_count to count_df
    count_df = count_df.merge(total_per_count, on=["balls", "strikes"], how="left")

    # ------------------------------------------
    # STEP 3.4: CALCULATE PERCENTAGE WITHIN COUNT
    # ------------------------------------------
    count_df["pct_in_count"] = (count_df["count"] / count_df["total_in_count"] * 100).round(1)

    # ------------------------------------------
    # STEP 3.5: SORT
    # ------------------------------------------
    return count_df.sort_values(["balls", "strikes", "pct_in_count"],
                                ascending=[True, True, False])


# ==============================================
# STEP 4: DOMINANT PITCH PER COUNT FUNCTION
# ==============================================
# Simplified version: only the MOST USED pitch in each count

def get_dominant_pitch_per_count(df: pd.DataFrame) -> pd.DataFrame:
    # df: pd.DataFrame → All pitches
    # -> pd.DataFrame → One row per count, with the dominant pitch

    """
    Returns the most used pitch type in each count.
    Used to build the heatmap in the dashboard.

    PARAMETERS:
    -----------
    df : pd.DataFrame
        All pitches

    RETURNS:
    --------
    pd.DataFrame
        One row per count (balls, strikes) with:
        - pitch_type: the most used
        - pitch_name_clean: human-readable name
        - pct_in_count: usage % in that count
    """

    # ------------------------------------------
    # STEP 4.1: GET FULL DISTRIBUTION
    # ------------------------------------------
    count_dist = get_count_distribution(df)
    if count_dist.empty:
        return pd.DataFrame()

    # ------------------------------------------
    # STEP 4.2: KEEP ONLY THE TOP (HIGHEST %) ROW PER COUNT
    # ------------------------------------------
    # 1. Sort by pct_in_count descending (highest to lowest)
    # 2. Group by (balls, strikes)
    # 3. .first() → take the first row of each group (the one with the highest %)

    dominant = (
        count_dist
        .sort_values("pct_in_count", ascending=False)
        .groupby(["balls", "strikes"])
        .first()
        .reset_index()
    )

    return dominant


# ==============================================
# STEP 5: MATCHUP BY BATTER HANDEDNESS FUNCTION
# ==============================================
# How does this pitcher perform against left-handed vs right-handed batters?

def get_matchup_metrics(df: pd.DataFrame) -> pd.DataFrame:
    # df: pd.DataFrame → All pitches
    # -> pd.DataFrame → One row per (pitch_type, stand)

    """
    Calculates metrics split by batter handedness.

    PARAMETERS:
    -----------
    df : pd.DataFrame
        All pitches

    RETURNS:
    --------
    pd.DataFrame
        Columns: pitch_type, pitch_name_clean, stand (L/R),
        uso_pct, whiff_rate, count, avg_velocity
    """

    if df.empty:
        return pd.DataFrame()

    # ------------------------------------------
    # STEP 5.1: CALCULATE TOTALS BY HANDEDNESS
    # ------------------------------------------
    # We need these totals to calculate usage percentages
    total_vs_left  = len(df[df["stand"] == "L"])   # Pitches vs left-handed batters
    total_vs_right = len(df[df["stand"] == "R"])   # Pitches vs right-handed batters

    # ------------------------------------------
    # STEP 5.2: GROUP BY PITCH TYPE AND HANDEDNESS
    # ------------------------------------------
    matchup = df.groupby(["pitch_type", "pitch_name_clean", "stand"]).agg(
        count=("pitch_type", "count"),              # Pitches of this type vs this handedness
        total_swings=("is_swing", "sum"),           # Swings at this pitch vs this handedness
        total_whiffs=("is_whiff", "sum"),           # Whiffs at this pitch vs this handedness
        avg_velocity=("release_speed", "mean"),     # Average velocity
    ).reset_index()

    # ------------------------------------------
    # STEP 5.3: CALCULATE USAGE % BY HANDEDNESS
    # ------------------------------------------
    # .apply() with lambda: applies a custom function to each row
    matchup["uso_pct"] = matchup.apply(
        lambda row: round(
            row["count"] / (total_vs_left if row["stand"] == "L" else total_vs_right) * 100, 1
        ), axis=1
    )
    # axis=1 means "apply to each row" (axis=0 would be each column)

    # LAMBDA EXPLANATION:
    # This anonymous function receives a row.
    # If row["stand"] is "L", it divides by total_vs_left; otherwise by total_vs_right.
    # Then multiplies by 100 and rounds to 1 decimal.

    # ------------------------------------------
    # STEP 5.4: CALCULATE WHIFF RATE BY HANDEDNESS
    # ------------------------------------------
    matchup["whiff_rate"] = (
        matchup["total_whiffs"] / matchup["total_swings"].replace(0, np.nan) * 100
    ).round(1)

    # ------------------------------------------
    # STEP 5.5: ROUND VELOCITY
    # ------------------------------------------
    matchup["avg_velocity"] = matchup["avg_velocity"].round(1)

    # ------------------------------------------
    # STEP 5.6: SORT
    # ------------------------------------------
    return matchup.sort_values(["pitch_type", "stand"]).reset_index(drop=True)


# ==============================================
# STEP 6: LOCATION DATA FUNCTION
# ==============================================
# Prepares data for the strike zone scatter plot

def get_location_data(df: pd.DataFrame, pitch_types: list = None, result_filter: str = "all") -> pd.DataFrame:
    # df: pd.DataFrame → All pitches
    # pitch_types: list → Filter by these pitch types (None = all)
    # result_filter: str → Type of outcome to include
    # -> pd.DataFrame → Data ready for the scatter plot

    """
    Filters and prepares location data (plate_x, plate_z) for the scatter plot.

    PARAMETERS:
    -----------
    df : pd.DataFrame
        All pitches
    pitch_types : list, optional
        List of pitch type codes to include. None = all.
    result_filter : str
        "all"    : all pitches
        "whiff"  : swinging strikes only
        "strike" : strikes (called + swinging)
        "hit"    : balls put in play only

    RETURNS:
    --------
    pd.DataFrame
        Columns: plate_x, plate_z, pitch_type, pitch_name_clean, description, stand
    """

    if df.empty:
        return pd.DataFrame()

    # ------------------------------------------
    # STEP 6.1: COPY TO AVOID MODIFYING ORIGINAL
    # ------------------------------------------
    filtered = df.copy()

    # ------------------------------------------
    # STEP 6.2: APPLY PITCH TYPE FILTER
    # ------------------------------------------
    if pitch_types:
        # If a list of types was provided, filter by those
        filtered = filtered[filtered["pitch_type"].isin(pitch_types)]

    # ------------------------------------------
    # STEP 6.3: APPLY RESULT FILTER
    # ------------------------------------------
    # Dictionary mapping the filter name to the description values
    result_map = {
        "whiff":  ["swinging_strike", "swinging_strike_blocked", "foul_tip"],
        "strike": ["swinging_strike", "swinging_strike_blocked", "called_strike", "foul_tip"],
        "hit":    ["hit_into_play", "hit_into_play_no_out", "hit_into_play_score"],
    }

    if result_filter in result_map:
        filtered = filtered[filtered["description"].isin(result_map[result_filter])]

    # ------------------------------------------
    # STEP 6.4: DROP ROWS WITHOUT COORDINATES
    # ------------------------------------------
    # To plot points we need X and Y. Rows missing either are useless.
    filtered = filtered.dropna(subset=["plate_x", "plate_z"])

    # ------------------------------------------
    # STEP 6.5: SELECT ONLY NECESSARY COLUMNS
    # ------------------------------------------
    return filtered[["plate_x", "plate_z", "pitch_type", "pitch_name_clean", "description", "stand"]].reset_index(drop=True)


# ==============================================
# STEP 7: SUMMARY KPIs FUNCTION
# ==============================================
# General pitcher summary (for the KPI cards at the top of the dashboard)

def get_summary_kpis(df: pd.DataFrame) -> dict:
    # df: pd.DataFrame → All pitches
    # -> dict → Dictionary with the KPIs

    """
    Calculates the general summary KPIs for the pitcher.

    PARAMETERS:
    -----------
    df : pd.DataFrame
        All pitches

    RETURNS:
    --------
    dict
        Dictionary with:
        - total_pitches: total number of pitches thrown
        - unique_pitch_types: how many different pitch types were used
        - global_whiff_rate: % of missed swings (all pitches)
        - primary_pitch: name of the most used pitch
        - primary_pitch_velo: velocity of that pitch
        - total_games: number of games pitched in
    """

    if df.empty:
        return {}

    # ------------------------------------------
    # STEP 7.1: BASIC METRICS
    # ------------------------------------------
    total_swings = df["is_swing"].sum()   # Total swings across all pitches
    total_whiffs = df["is_whiff"].sum()   # Total missed swings

    # ------------------------------------------
    # STEP 7.2: PRIMARY PITCH
    # ------------------------------------------
    # .value_counts() counts how many times each pitch_type appears.
    # .idxmax() returns the index (pitch_type) of the maximum value.
    primary_pitch_type = df["pitch_type"].value_counts().idxmax()

    # Look up the human-readable name for that pitch_type
    primary_pitch_name = df.loc[df["pitch_type"] == primary_pitch_type, "pitch_name_clean"].iloc[0]

    # Average velocity of that pitch
    primary_velo = df.loc[df["pitch_type"] == primary_pitch_type, "release_speed"].mean()

    # ------------------------------------------
    # STEP 7.3: CALCULATE UNIQUE GAMES
    # ------------------------------------------
    # .nunique() counts unique values.
    # .dt.date extracts only the date (without time).
    if "game_date" in df.columns:
        total_games = df["game_date"].dt.date.nunique()
    else:
        total_games = 0

    # ------------------------------------------
    # STEP 7.4: BUILD AND RETURN THE DICTIONARY
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
# FINAL NOTE: WHY DO WE RETURN DATAFRAMES AND DICTS?
# ==============================================
# - DataFrames: when we have TABLE data (multiple rows, multiple columns)
#   Example: metrics by pitch type, matchup by handedness
#
# - Dicts: when we have INDIVIDUAL VALUES that do not form a table
#   Example: global KPIs (total_pitches, primary_pitch, etc.)
#
# This consistency means charts.py and app.py always know WHAT to expect
# from each function.