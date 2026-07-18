"""Fast verification using only sample data (147 rows) for quick testing."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.data_manager import data_manager
from app import training
from app.feature_store import FeatureStore
from app.engine import Threshold, derive_markets, derive_combinations, qualify_and_rank
from app.persistence import load_thresholds
from app import db


def main():
    print("=== 1. Provider status ===")
    print(json.dumps(data_manager.provider_status(), indent=2))

    print("\n=== 2. Kaggle historical import (sample only) ===")
    # Use only EPL for faster testing
    fixtures = data_manager.import_historical(["EPL"])
    # Filter to only use the sample file (147 rows) for faster testing
    # The sample file has '2023_2024' in the name
    sample_fixtures = [f for f in fixtures if "2023_2024" in f.external_id or f.season_name == "2023/2024"]
    # If no sample file, just use first 500 fixtures
    if len(sample_fixtures) < 50:
        sample_fixtures = fixtures[:500]
    print(f"Using {len(sample_fixtures)} fixtures for fast training")
    print("Sample:", sample_fixtures[0].home_team, "vs", sample_fixtures[0].away_team,
          sample_fixtures[0].home_score, "-", sample_fixtures[0].away_score)

    print("\n=== 3. Feature engineering ===")
    store = FeatureStore()
    X, y, _ = training.build_matrix(sample_fixtures, store)
    print(f"Feature matrix: {X.shape[0]} rows x {X.shape[1]} features")
    print("Feature names (first 10):", X.columns[:10].tolist())
    assert X.shape[0] >= 50, "need >=50 samples"
    assert X.shape[1] >= 20, "need >=20 features"

    print("\n=== 4. Model training (scaling + CV + split) ===")
    res = training.train(sample_fixtures, model_name="logreg")  # Use faster logistic regression
    print(json.dumps(res, indent=2, default=str))
    assert res.get("modelVersion"), "training failed"
    assert res["metrics"]["test_accuracy"] > 0

    print("\n=== 5. Load model + generate predictions ===")
    bundle = training.load_model()
    print("Loaded model version:", bundle["version"], "features:", len(bundle["features"]))

    # Build a prediction from a finished fixture using its normalized features
    from app.feature_pipeline import fixtures_to_dataframe, build_contexts
    df = fixtures_to_dataframe(sample_fixtures)
    contexts = build_contexts(df)
    feats_df = store.compute_batch(contexts)
    import pandas as pd
    single = feats_df.iloc[[-1]][bundle["features"]]
    proba = bundle["pipeline"].predict_proba(single)[0]
    home, draw, away = float(proba[0]), float(proba[1]), float(proba[2])

    thr = load_thresholds()
    thresholds = Threshold(MATCH_RESULT=thr["MATCH_RESULT"], DOUBLE_CHANCE=thr["DOUBLE_CHANCE"],
                           OTHER=thr["OTHER"], COMBINATION=thr["COMBINATION"])
    base = derive_markets(home, draw, away, {"btts": 0.55})
    combos = derive_combinations(base)
    qualified = qualify_and_rank(base + combos, thresholds)
    print(f"\nSample 1X2: HOME={home:.2f} DRAW={draw:.2f} AWAY={away:.2f}")
    print(f"Qualified predictions for sample fixture: {len(qualified)}")
    for p in qualified[:5]:
        print(f"  - {p.market}/{p.selection}: conf {p.confidence:.1f}%")

    print("\n=== VERIFICATION PASSED ===")
    return res


if __name__ == "__main__":
    main()