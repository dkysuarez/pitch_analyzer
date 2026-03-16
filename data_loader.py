"""
data_loader.py
==============
Responsibility: Connect to Baseball Savant via pybaseball,
fetch Statcast data for a pitcher by season, clean it,
and return a DataFrame ready for metric calculations.

No business logic here — ingestion and cleaning only.
"""

import pandas as pd
import streamlit as st
import pybaseball as pb

# Columns actually used in the project.
# All other Statcast columns are dropped to keep the DataFrame lightweight.
COLUMNS_NEEDED = [
    "game_date",
    "pitcher",
    "player_name",
    "pitch_type",        # Pitch type code: FF, SL, CH, CU, SI, FC, FS
    "pitch_name",        # Human-readable name: 4-Seam Fastball, Slider, etc.
    "release_speed",     # Velocity in MPH
    "release_spin_rate", # Spin rate in RPM
    "plate_x",           # Horizontal coordinate at home plate
    "plate_z",           # Vertical coordinate at home plate
    "description",       # Outcome: swinging_strike, called_strike, ball, hit_into_play, etc.
    "balls",             # Ball count before the pitch
    "strikes",           # Strike count before the pitch
    "stand",             # Batter handedness: L (left) or R (right)
    "events",            # Final at-bat result if applicable (strikeout, single, etc.)
    "zone",              # Strike zone location (1-9 inside, 11-14 outside)
    "type",              # Simple classification: S (strike), B (ball), X (in play)
]

# Mapping from pitch type codes to human-readable names for the dashboard
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


# ─── Main function ────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading data from Baseball Savant...")
def load_pitcher_data(pitcher_id: int, season: int) -> pd.DataFrame:
    """
    Downloads and cleans Statcast data for a pitcher for a given season.

    Parameters
    ----------
    pitcher_id : int
        MLB ID of the pitcher (e.g., 543037 for Gerrit Cole).
    season : int
        Season to query (e.g., 2023).

    Returns
    -------
    pd.DataFrame
        Clean DataFrame with only the required columns,
        no rows with null pitch_type, ready for metric calculations.
    """
    # Regular season start and end dates
    start_date = f"{season}-03-20"
    end_date   = f"{season}-10-05"

    # Call Baseball Savant via pybaseball.
    # Returns one row per pitch thrown by this pitcher.
    raw_df = pb.statcast_pitcher(
        start_dt=start_date,
        end_dt=end_date,
        player_id=pitcher_id
    )

    if raw_df is None or raw_df.empty:
        return pd.DataFrame()  # Empty DataFrame — the app handles this case

    # Keep only the columns we use
    existing_cols = [c for c in COLUMNS_NEEDED if c in raw_df.columns]
    df = raw_df[existing_cols].copy()

    # Drop rows without a pitch type (result rows, not actual pitches)
    df = df[df["pitch_type"].notna() & (df["pitch_type"] != "")]

    # Parse game date
    df["game_date"] = pd.to_datetime(df["game_date"])

    # Keep only valid batter handedness — L and R, discard ambiguous values
    df = df[df["stand"].isin(["L", "R"])]

    # Helper column: was it a swinging strike? (needed for whiff_rate)
    df["is_whiff"] = df["description"].isin([
        "swinging_strike",
        "swinging_strike_blocked",
        "foul_tip"  # foul tip with 2 strikes also counts as a whiff
    ])

    # Helper column: was it a swing? (to calculate whiff_rate correctly)
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

    # Helper column: was it a called strike?
    df["is_called_strike"] = df["description"] == "called_strike"

    # Human-readable pitch type name for charts
    df["pitch_name_clean"] = df["pitch_type"].map(PITCH_TYPE_NAMES).fillna(df["pitch_type"])

    return df


# ─── Pitcher search by name ───────────────────────────────────────────────────

@st.cache_data(show_spinner="Searching pitcher...")
def search_pitcher(name: str) -> pd.DataFrame:
    """
    Searches for a pitcher by name using the pybaseball player registry.

    Parameters
    ----------
    name : str
        Full or partial pitcher name (e.g., "Gerrit Cole").

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: name_first, name_last, key_mlbam (MLB ID), mlb_played_last.
        Filtered to pitchers active since 2015 (Statcast era).
    """
    results = pb.playerid_lookup(
        last=name.split()[-1],
        first=name.split()[0] if len(name.split()) > 1 else ""
    )

    if results is None or results.empty:
        return pd.DataFrame()

    # Keep only relevant fields
    cols = ["name_first", "name_last", "key_mlbam", "mlb_played_last"]
    existing = [c for c in cols if c in results.columns]
    results = results[existing].copy()

    # Filter to players active in the Statcast era (2015 onward)
    if "mlb_played_last" in results.columns:
        results = results[results["mlb_played_last"] >= 2015]

    return results.reset_index(drop=True)


# ─── Validation utilities ─────────────────────────────────────────────────────

def validate_dataframe(df: pd.DataFrame) -> dict:
    """
    Validates that the DataFrame has the minimum required content
    to calculate metrics.

    Returns
    -------
    dict with keys:
        - valid (bool): True if the DataFrame is usable
        - message (str): Description of the problem if invalid
        - pitch_count (int): Total number of pitches in the DataFrame
    """
    if df is None or df.empty:
        return {
            "valid": False,
            "message": "No data found for this pitcher and season.",
            "pitch_count": 0
        }

    if "pitch_type" not in df.columns:
        return {
            "valid": False,
            "message": "DataFrame does not contain the pitch_type column.",
            "pitch_count": 0
        }

    pitch_count = len(df)
    if pitch_count < 50:
        return {
            "valid": False,
            "message": f"Only {pitch_count} pitches found. Minimum 50 required for reliable analysis.",
            "pitch_count": pitch_count
        }

    return {"valid": True, "message": "OK", "pitch_count": pitch_count}