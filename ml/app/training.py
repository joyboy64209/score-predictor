"""ML training pipeline: feature scaling, encoding, train/val/test split,
cross-validation, model versioning + dataset versioning, persistence.

Replaces the old synthetic trainer. Trains on normalized historical fixtures
(from any provider) and persists a model + metrics for the prediction API."""

import datetime as dt
import hashlib
import json
import os
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, log_loss
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .config import settings
from .feature_pipeline import build_matrix, train_val_test_split
from .feature_store import FeatureStore
from .schemas import Fixture


MODEL_REGISTRY = {
    "logreg": LogisticRegression(max_iter=1000),
    "random_forest": RandomForestClassifier(n_estimators=200, random_state=42),
    "gradient_boosting": GradientBoostingClassifier(n_estimators=200, max_depth=3, random_state=42),
}


def dataset_fingerprint(fixtures: list[Fixture]) -> str:
    ids = sorted(f.external_id for f in fixtures)
    raw = "|".join(ids).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def train(fixtures: list[Fixture],
          model_name: str = "gradient_boosting",
          store: Optional[FeatureStore] = None,
          lookups: Optional[dict] = None) -> dict:
    """Train a 1X2 classifier. Returns a result dict with metrics + paths."""
    store = store or FeatureStore()
    lookups = lookups or {}
    X, y, _ = build_matrix(fixtures, store, **lookups)
    if len(X) < 50:
        raise ValueError(f"Not enough training samples ({len(X)}); need >= 50")
    if len({int(v) for v in y}) < 2:
        raise ValueError("Need at least two outcome classes to train")

    X_train, X_val, X_test, y_train, y_val, y_test = train_val_test_split(X, y)

    base = MODEL_REGISTRY[model_name]
    pipeline = Pipeline([("scaler", StandardScaler()), ("clf", base)])

    # Cross-validation on the training set
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="accuracy")

    pipeline.fit(X_train, y_train)
    pred_val = pipeline.predict(X_val)
    pred_test = pipeline.predict(X_test)

    metrics = {
        "cv_accuracy_mean": float(cv_scores.mean()),
        "cv_accuracy_std": float(cv_scores.std()),
        "val_accuracy": float(accuracy_score(y_val, pred_val)),
        "test_accuracy": float(accuracy_score(y_test, pred_test)),
        "test_f1_macro": float(f1_score(y_test, pred_test, average="macro")),
        "test_log_loss": float(log_loss(y_test, pipeline.predict_proba(X_test))),
        "n_train": int(len(X_train)),
        "n_val": int(len(X_val)),
        "n_test": int(len(X_test)),
        "features": list(X.columns),
    }

    model_dir = settings.model_dir_abs
    os.makedirs(model_dir, exist_ok=True)
    version = f"v2-{dataset_fingerprint(fixtures)}-{model_name}"
    model_path = os.path.join(model_dir, f"model_{version}.joblib")
    joblib.dump({"pipeline": pipeline, "features": list(X.columns),
                 "model_name": model_name, "version": version}, model_path)

    # persist dataset snapshot + feature stats
    meta = {
        "version": version,
        "model_name": model_name,
        "dataset_fingerprint": dataset_fingerprint(fixtures),
        "n_samples": int(len(X)),
        "metrics": metrics,
        "trained_at": dt.datetime.utcnow().isoformat() + "Z",
        "feature_means": X.mean().to_dict(),
    }
    with open(os.path.join(model_dir, f"meta_{version}.json"), "w") as f:
        json.dump(meta, f, indent=2, default=str)

    return {
        "modelVersion": version,
        "algorithm": model_name,
        "metrics": metrics,
        "path": model_path,
        "featureCount": int(X.shape[1]),
    }


def load_model(version: Optional[str] = None):
    model_dir = settings.model_dir_abs
    if version:
        path = os.path.join(model_dir, f"model_{version}.joblib")
    else:
        files = sorted(
            [f for f in os.listdir(model_dir) if f.startswith("model_")],
            reverse=True,
        ) if os.path.exists(model_dir) else []
        if not files:
            raise FileNotFoundError("No trained model found. Run training first.")
        path = os.path.join(model_dir, files[0])
    return joblib.load(path)


def list_versions() -> list[dict]:
    model_dir = settings.model_dir_abs
    if not os.path.exists(model_dir):
        return []
    out = []
    for f in os.listdir(model_dir):
        if f.startswith("meta_") and f.endswith(".json"):
            with open(os.path.join(model_dir, f)) as fh:
                out.append(json.load(fh))
    return sorted(out, key=lambda m: m.get("trained_at", ""), reverse=True)
