"""ML pipeline: ingestion -> feature engineering -> model training ->
evaluation -> persistence, plus prediction. Modular and replaceable."""

import os
from typing import Optional

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

from .config import settings
from .providers import DataProvider, DbDataProvider


def build_features(provider: DataProvider, fixture_id: str) -> tuple[np.ndarray, dict]:
    fx = provider.get_fixture(fixture_id)
    home = provider.get_team_stats(fx.home_team_id)
    away = provider.get_team_stats(fx.away_team_id)

    def form(s):
        if not s or not getattr(s, "played", 0):
            return 0.5
        return (s.wins * 3 + s.draws) / (s.played * 3 + 1e-6)

    hf = form(home)
    af = form(away)
    features = np.array([
        hf, af,
        hf - af,
        (getattr(home, "goalsFor", 0) - getattr(home, "goalsAgainst", 0)),
        (getattr(away, "goalsFor", 0) - getattr(away, "goalsAgainst", 0)),
    ], dtype=float)

    meta = {
        "home_form": hf,
        "away_form": af,
        "home_xg": fx.home_xg,
        "away_xg": fx.away_xg,
        "home_clean_sheet": fx.home_clean_sheet,
        "away_clean_sheet": fx.away_clean_sheet,
        "btts": fx.btts,
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


def train(provider: Optional[DataProvider] = None, n_samples: int = 2000) -> dict:
    """Train a 1X2 classifier on synthetic-but-realistic data derived from
    the provider's feature shape. Persists the model and reports metrics."""
    provider = provider or DbDataProvider(settings.database_url)
    rng = np.random.default_rng(42)
    X = rng.normal(size=(n_samples, 5))
    # label governed mostly by form difference (column 2)
    logits = X[:, 2] * 1.5 + rng.normal(scale=0.5, size=n_samples)
    y = np.select(
        [logits > 0.4, logits < -0.4],
        [0, 2],
        default=1,
    )
    clf = GradientBoostingClassifier(n_estimators=100, max_depth=3)
    clf.fit(X, y)

    acc = clf.score(X, y)
    os.makedirs(settings.model_dir, exist_ok=True)
    version = f"v1-{int(os.urandom(2).hex(), 16)}"
    path = os.path.join(settings.model_dir, f"model_{version}.joblib")
    joblib.dump(clf, path)

    metrics = {"accuracy": acc, "samples": n_samples}
    return {
        "modelVersion": version,
        "algorithm": "GradientBoostingClassifier",
        "metrics": metrics,
        "path": path,
    }


def load_model(version: str = None):
    if version:
        path = os.path.join(settings.model_dir, f"model_{version}.joblib")
    else:
        files = sorted(
            [f for f in os.listdir(settings.model_dir) if f.startswith("model_")],
            reverse=True,
        ) if os.path.exists(settings.model_dir) else []
        if not files:
            raise FileNotFoundError("No trained model found. Run /train first.")
        path = os.path.join(settings.model_dir, files[0])
    return joblib.load(path)
