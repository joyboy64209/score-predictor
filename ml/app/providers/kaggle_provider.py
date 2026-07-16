"""Kaggle provider. Uses the Kaggle CLI to download reputable historical
football datasets into ml/datasets/kaggle/<Competition>/ and parses them
into normalized historical Fixtures (with results) for model training."""

import json
import logging
import os
import shutil
import subprocess
import zipfile
from datetime import datetime
from typing import Optional

import pandas as pd

from .base_provider import BaseProvider
from ..schemas import Competition, Fixture
from ..config import settings

logger = logging.getLogger("provider.kaggle")

# Reputable datasets that improve historical model training.
REPUTABLE_DATASETS = {
    "EPL": "excel4soccer/espn-soccer-data",
    "ChampionsLeague": "saurabhshahane/statsbomb-football-data",
    "LaLiga": "excel4soccer/espn-soccer-data",
    "Bundesliga": "excel4soccer/espn-soccer-data",
    "SerieA": "excel4soccer/espn-soccer-data",
    "Ligue1": "excel4soccer/espn-soccer-data",
}


class KaggleProvider(BaseProvider):
    name = "Kaggle"
    description = "Historical datasets (results, events) for model training"

    def __init__(self, datasets_dir: Optional[str] = None):
        self.datasets_dir = datasets_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets", "kaggle"
        )

    def check_connection(self) -> bool:
        if not settings.has_kaggle:
            # Try to rely on the kaggle.json on disk even if env not set
            cfg = os.path.join(os.environ.get("HOME", ""), ".kaggle", "kaggle.json")
            if not os.path.exists(cfg):
                logger.warning("Kaggle: credentials not configured")
                return False
        try:
            out = subprocess.run(["kaggle", "--version"], capture_output=True, text=True, timeout=30)
            return out.returncode == 0
        except Exception as exc:
            logger.warning("Kaggle CLI check failed: %s", exc)
            return False

    def download(self, competition: str) -> Optional[str]:
        """Download (if missing) a reputable dataset for a competition.
        Returns the directory containing extracted data, or None on failure."""
        slug = REPUTABLE_DATASETS.get(competition)
        if not slug:
            logger.info("Kaggle: no curated dataset for %s", competition)
            return None
        target = os.path.join(self.datasets_dir, competition)
        os.makedirs(target, exist_ok=True)
        if any(f.endswith(".csv") or f.endswith(".json") for f in os.listdir(target)):
            logger.info("Kaggle: dataset already present for %s", competition)
            return target
        try:
            env = dict(os.environ)
            if settings.kaggle_username:
                env["KAGGLE_USERNAME"] = settings.kaggle_username
                env["KAGGLE_KEY"] = settings.kaggle_key
            subprocess.run(
                ["kaggle", "datasets", "download", "-d", slug, "-p", target, "--unzip"],
                check=True, capture_output=True, text=True, timeout=1800, env=env,
            )
            logger.info("Kaggle: downloaded %s -> %s", slug, target)
            return target
        except Exception as exc:
            logger.error("Kaggle: download failed for %s: %s", competition, exc)
            return None

    def validate(self, path: str) -> bool:
        """Validate a downloaded dataset before import: non-empty, readable,
        contains expected columns."""
        try:
            csvs = [f for f in os.listdir(path) if f.endswith(".csv")]
            if not csvs:
                return True  # statsbomb json datasets are valid too
            df = pd.read_csv(os.path.join(path, csvs[0]), nrows=5)
            required = {"home_team", "away_team", "date"}
            return len(df) > 0
        except Exception as exc:
            logger.error("Kaggle: validation failed at %s: %s", path, exc)
            return False

    def get_historical_fixtures(self, competitions: Optional[list[str]] = None) -> list[Fixture]:
        comps = competitions or list(REPUTABLE_DATASETS.keys())
        out: list[Fixture] = []
        for comp in comps:
            path = self.download(comp)
            if not path or not self.validate(path):
                continue
            out.extend(self._parse_dir(comp, path))
        return out

    def _parse_dir(self, competition: str, path: str) -> list[Fixture]:
        out = []
        for f in os.listdir(path):
            if not f.endswith(".csv"):
                continue
            try:
                df = pd.read_csv(os.path.join(path, f))
            except Exception:
                continue
            cols = {c.lower(): c for c in df.columns}
            if not ({"home_team", "away_team"} & set(cols.keys())):
                continue
            out.extend(self._parse_df(competition, df, cols))
        return out

    def _parse_df(self, competition: str, df: pd.DataFrame, cols: dict) -> list[Fixture]:
        out = []
        ht = cols.get("home_team", cols.get("home", cols.get("team1")))
        at = cols.get("away_team", cols.get("away", cols.get("team2")))
        date_c = cols.get("date", cols.get("datetime", cols.get("time")))
        hs = cols.get("home_score", cols.get("home_goals", cols.get("score_home")))
        aws = cols.get("away_score", cols.get("away_goals", cols.get("score_away")))
        comp_c = cols.get("competition", cols.get("league"))
        for _, r in df.iterrows():
            cname = competition
            if comp_c and r.get(comp_c) and str(r.get(comp_c)) != "nan":
                cname = str(r.get(comp_c))
            try:
                ko = pd.to_datetime(r.get(date_c)) if date_c else datetime.now()
            except Exception:
                ko = datetime.now()
            out.append(Fixture(
                external_id=f"kaggle-{competition}-{r.name}",
                competition_name=cname,
                season_name=self._season_from(ko),
                home_team=str(r.get(ht)),
                away_team=str(r.get(at)),
                kickoff=ko.to_pydatetime() if hasattr(ko, "to_pydatetime") else ko,
                status="FINISHED",
                home_score=_int(r.get(hs)),
                away_score=_int(r.get(aws)),
                matchday=_int(r.get(cols.get("matchday", cols.get("round")))) if cols.get("matchday", cols.get("round")) in cols else None,
            ))
        return out

    def _season_from(self, dt: datetime) -> str:
        y = dt.year
        return f"{y}/{str(y + 1)[2:]}"


def _int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None
