# ⚾ Pitch Effectiveness Analyzer

> Real-time MLB pitching analysis powered by Baseball Savant Statcast data.

---

## What it does

Pitch Effectiveness Analyzer is an interactive web dashboard that lets scouts, analysts, and baseball fans explore **how effective a pitcher's arsenal really is** — without writing a single line of code.

You pick a pitcher. You pick a season. The app pulls real Statcast data and breaks down every pitch they threw: how often they used it, how hard batters swung and missed, where they located it in the zone, and how it performed against left vs. right-handed batters.

---

## Why it matters

Traditional scouting reports take hours to build manually. Statcast data is publicly available but scattered and technical. This tool bridges that gap — turning thousands of raw pitch-by-pitch records into clear, actionable insights in under 30 seconds.

| Without this tool | With this tool |
|---|---|
| Download CSVs manually from Baseball Savant | One search, data loads automatically |
| Write Python to calculate whiff rate | Interactive table with all metrics |
| Build charts from scratch | Six ready-to-use visualizations |
| Guess which pitch works vs. lefties | Side-by-side L vs R comparison |

---

## Features

**Arsenal Overview**
Horizontal bar chart showing usage % for every pitch type the pitcher threw. See their full repertoire at a glance.

**Velocity Chart**
Lollipop chart comparing average velocity across pitch types. Instantly see how much harder the fastball is than the changeup.

**Effectiveness Metrics Table**
One row per pitch type with: usage %, average velocity, spin rate, whiff rate, called strike %, and put-away rate (strikeout rate with 2 strikes). Rendered with Streamlit progress bars for quick visual scanning.

**Count Heatmap**
4×3 heatmap (0–3 balls × 0–2 strikes) showing the dominant pitch and its usage % in every count. Answers the key scouting question: *what does this pitcher throw when the pressure is on?*

**Matchup by Batter Handedness**
Grouped bar chart comparing whiff rate and usage % against left-handed vs. right-handed batters for each pitch type. Essential for lineup construction decisions.

**Pitch Location Scatter**
Interactive scatter plot of every pitch on the strike zone, colored by pitch type. Filter by outcome (all, whiffs only, strikes only, balls in play). Toggle individual pitch types from the legend.

---

## Stack

| Layer | Technology |
|---|---|
| Data source | [Baseball Savant](https://baseballsavant.mlb.com) via [pybaseball](https://github.com/jldbc/pybaseball) |
| Data processing | pandas, numpy |
| Visualizations | Plotly Graph Objects |
| Dashboard | Streamlit |
| Language | Python 3.10+ |

All data is **free and publicly available**. No API key required.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/pitch_analyzer.git
cd pitch_analyzer

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Quick Start

1. Type a pitcher's name in the sidebar (e.g. **Gerrit Cole**)
2. Select a season (2019–2024)
3. Choose batter handedness filter if needed
4. Explore — every chart updates instantly

> **First load tip:** pybaseball fetches data directly from Baseball Savant. The first query for a pitcher/season combination takes 5–15 seconds. Subsequent loads are cached instantly.

---

## Project Structure

```
pitch_analyzer/
├── app.py            # Streamlit dashboard — entry point
├── data_loader.py    # Statcast data ingestion and caching
├── metrics.py        # Metric calculations (whiff rate, put-away rate, etc.)
├── charts.py         # Plotly visualizations
├── requirements.txt  # Python dependencies
└── README.md
```

---

## Metrics Reference

| Metric | Definition |
|---|---|
| **Whiff Rate %** | % of swings that result in a miss |
| **Put-Away Rate %** | % of pitches with 2 strikes that end in a strikeout |
| **Called Strike %** | % of pitches called a strike without a swing |
| **Usage %** | Share of total pitches thrown of this type |
| **Avg Velocity** | Mean release speed in MPH |
| **Spin Rate** | Mean spin rate in RPM |

---

## Data Coverage

- Seasons: **2019 – 2024** (regular season only)
- Pitchers: Any MLB pitcher with Statcast data
- Source: Baseball Savant — updated daily during the season

---

*Built as a Data Analytics Mentorship Project · Data from Baseball Savant (Statcast)*