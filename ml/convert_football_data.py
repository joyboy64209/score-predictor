"""Convert football-data.co.uk Excel files to CSV format expected by KaggleProvider.

Maps:
  HomeTeam -> home_team
  AwayTeam -> away_team
  Date -> date
  FTHG -> home_score
  FTAG -> away_score
  FTR -> result (H/D/A)
  Div -> competition (E0=EPL, SP=LaLiga, D1=Bundesliga, I1=SerieA, F1=Ligue1)
"""

import os
import pandas as pd

# Division to competition mapping (football-data.co.uk codes)
DIV_MAP = {
    "E0": "EPL",
    "E1": "EPL",
    "SP": "LaLiga",
    "D1": "Bundesliga",
    "I1": "SerieA",
    "F1": "Ligue1",
    "CL": "ChampionsLeague",
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "datasets", "kaggle")

def convert_file(xls_path: str) -> None:
    """Convert a single Excel file to CSV(s) per competition."""
    try:
        df = pd.read_excel(xls_path)
    except Exception as e:
        print(f"Failed to read {xls_path}: {e}")
        return

    if "Div" not in df.columns:
        print(f"No 'Div' column in {xls_path}, skipping")
        return

    for div, comp in DIV_MAP.items():
        comp_df = df[df["Div"] == div].copy()
        if comp_df.empty:
            continue

        # Rename columns to match KaggleProvider expectations
        comp_df = comp_df.rename(columns={
            "HomeTeam": "home_team",
            "AwayTeam": "away_team",
            "Date": "date",
            "FTHG": "home_score",
            "FTAG": "away_score",
        })

        # Select only the columns we need
        out_cols = ["home_team", "away_team", "date", "home_score", "away_score"]
        comp_df = comp_df[out_cols]

        # Create output directory
        out_dir = os.path.join(OUTPUT_BASE, comp)
        os.makedirs(out_dir, exist_ok=True)

        # Write CSV
        out_name = f"historical_{os.path.basename(xls_path).replace('.xlsx', '').replace('.xls', '')}.csv"
        out_path = os.path.join(out_dir, out_name)
        comp_df.to_csv(out_path, index=False)
        print(f"Wrote {len(comp_df)} rows to {out_path}")

def main():
    for f in sorted(os.listdir(DATA_DIR)):
        if f.endswith((".xls", ".xlsx")):
            convert_file(os.path.join(DATA_DIR, f))
    print("Done!")

if __name__ == "__main__":
    main()