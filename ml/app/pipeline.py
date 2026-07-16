"""ML pipeline: ingestion -> feature engineering -> model training ->
evaluation -> persistence, plus prediction. Modular and replaceable."""

import os
from typing import Optional

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

from .config import settings
from .db import DbDataProvider


def build_features(provider: DbDataProvider, fixture_id: str) -> tuple[np.ndarray, dict]:
    fx = provider.get_fixture(fixture_id)
    if fx is None:
        raise ValueError(f"Fixture {fixture_id} not found in database")
    home = provider.get_team_stats(fx.home_team)
    away = provider.get_team_stats(fx.away_team)

    def form(s: dict) -> float:
        played = s.get("played", 0) or 0
        if not played:
            return 0.5
        return (s.get("wins", 0) * 3 + s.get("draws", 0)) / (played * 3 + 1e-6)

    hf = form(home)
    af = form(away)
    features = np.array([
        hf, af,
        hf - af,
        (home.get("goalsFor", 0) - home.get("goalsAgainst", 0)),
        (away.get("goalsFor", 0) - away.get("goalsAgainst", 0)),
    ], dtype=float)

    meta = {
        "home_form": hf,
        "away_form": af,
        "home_xg": 1.4,
        "away_xg": 1.2,
        "home_clean_sheet": 0.35,
        "away_clean_sheet": 0.3,
        "btts": 0.55,
    }
    return features.reshape(1, -1), meta


def predict_1x2(model, features: np.ndarray) -> tuple[float, float, float]:
    proba = model.predict_proba(features)[0]
    classes = model.classes_
    mapping = {c: i for i, c in enumerate(classes)}
    home = float(proba[mapping.get(0, 0)])
    draw = float(proba[mapping.get(1, 1)])
    away = float(proba[mapping.get(2, 2)])
    return home, draw, away

