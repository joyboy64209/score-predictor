"""Builds training/serving matrices from normalized fixtures using the
FeatureStore. Handles: rolling form windows, merging standings / advanced
metrics / Elo, encoding, scaling, train/val/test split and dataset
versioning. Missing values are handled inside the FeatureStore."""

from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from .feature_store import FeatureStore, MatchContext
from .schemas import Fixture


LABEL_MAP = {"HOME": 0, "DRAW": 1, "AWAY": 2}


def fixtures_to_dataframe(fixtures: list[Fixture]) -> pd.DataFrame:
    """Flatten normalized fixtures (with results) into a per-match row."""
    rows = []
    for f in fixtures:
        if f.home_score is None or f.away_score is None:
            continue
        total = f.home_score + f.away_score
        if f.home_score > f.away_score:
            result = "HOME"
        elif f.home_score < f.away_score:
            result = "AWAY"
        else:
            result = "DRAW"
        rows.append({
            "fixture_id": f.external_id,
            "home_team": f.home_team,
            "away_team": f.away_team,
            "competition": f.competition_name,
            "season": f.season_name,
            "kickoff": f.kickoff,
            "home_score": f.home_score,
            "away_score": f.away_score,
            "total_goals": total,
            "result": result,
            "label": LABEL_MAP[result],
            "btts": int(f.home_score > 0 and f.away_score > 0),
        })
    return pd.DataFrame(rows)


def build_contexts(df: pd.DataFrame,
                    standings: Optional[dict] = None,
                    advanced: Optional[dict] = None,
                    elo: Optional[dict] = None,
                    injuries: Optional[dict] = None,
                    suspensions: Optional[dict] = None) -> list[MatchContext]:
    """For each match, compute rolling form for both teams and assemble a
    MatchContext. Form windows use matches that occurred before kickoff."""
    standings = standings or {}
    advanced = advanced or {}
    elo = elo or {}
    injuries = injuries or {}
    suspensions = suspensions or {}
    df = df.sort_values("kickoff").reset_index(drop=True)
    contexts: list[MatchContext] = []
    for i, row in df.iterrows():
        ht, at = row["home_team"], row["away_team"]
        ko = row["kickoff"]
        home_hist = _history_before(df, ht, ko)
        away_hist = _history_before(df, at, ko)
        home_hist = _tag_side(home_hist, ht)
        away_hist = _tag_side(away_hist, at)
        ctx = MatchContext(
            row=row.to_dict(),
            home_last=home_hist,
            away_last=away_hist,
            home_standing=standings.get(ht),
            away_standing=standings.get(at),
            home_advanced=advanced.get(ht),
            away_advanced=advanced.get(at),
            home_elo=elo.get(ht),
            away_elo=elo.get(at),
            home_injuries=len(injuries.get(ht, [])),
            away_injuries=len(injuries.get(at, [])),
            home_suspensions=len(suspensions.get(ht, [])),
            away_suspensions=len(suspensions.get(at, [])),
        )
        contexts.append(ctx)
    return contexts


def _history_before(df: pd.DataFrame, team: str, ko) -> pd.DataFrame:
    mask = (((df["home_team"] == team) | (df["away_team"] == team)) &
            (df["kickoff"] < ko))
    sub = df[mask].copy()
    sub["result"] = sub.apply(lambda r: _team_result(r, team), axis=1)
    return sub.sort_values("kickoff").tail(10)


def _team_result(r, team):
    if r["home_team"] == team:
        return "W" if r["home_score"] > r["away_score"] else ("L" if r["home_score"] < r["away_score"] else "D")
    else:
        return "W" if r["away_score"] > r["home_score"] else ("L" if r["away_score"] < r["home_score"] else "D")


def _tag_side(df: pd.DataFrame, team: str) -> pd.DataFrame:
    out = df.copy()
    out["is_home"] = out["home_team"] == team
    return out


def build_matrix(fixtures: list[Fixture], store: Optional[FeatureStore] = None,
                 **lookups) -> tuple[pd.DataFrame, np.ndarray, FeatureStore]:
    store = store or FeatureStore()
    df = fixtures_to_dataframe(fixtures)
    if df.empty:
        return df, np.array([]), store
    contexts = build_contexts(df, **lookups)
    features = store.compute_batch(contexts)
    labels = df["label"].values
    return features, labels, store


def train_val_test_split(X: pd.DataFrame, y: np.ndarray, test_size: float = 0.15,
                         val_size: float = 0.15, random_state: int = 42):
    from sklearn.model_selection import train_test_split
    X_train, X_tmp, y_train, y_tmp = train_test_split(
        X, y, test_size=test_size + val_size, random_state=random_state, stratify=y)
    vr = val_size / (test_size + val_size)
    X_val, X_test, y_val, y_test = train_test_split(
        X_tmp, y_tmp, test_size=1 - vr, random_state=random_state, stratify=y_tmp)
    return X_train, X_val, X_test, y_train, y_val, y_test
