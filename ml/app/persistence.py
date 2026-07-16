"""Persist predictions back to Postgres so the backend can read them."""

from typing import Optional

from .config import settings
from .engine import Prediction


def persist_predictions(fixture_id: str, predictions: list[Prediction], model_version: str):
    from sqlalchemy import create_engine, text, insert
    engine = create_engine(settings.database_url)
    rows = []
    for p in predictions:
        rows.append({
            "id": f"{fixture_id}:{p.market}:{p.selection}",
            "fixtureId": fixture_id,
            "market": p.market,
            "selection": p.selection,
            "probability": round(p.probability, 4),
            "confidence": round(p.confidence, 2),
            "expectedValue": round(p.expected_value, 4) if p.expected_value is not None else None,
            "status": p.status,
            "reasons": {"factors": p.reasons},
            "modelVersion": model_version,
        })
    with engine.begin() as conn:
        conn.execute(text('DELETE FROM "Prediction" WHERE "fixtureId" = :fid'), {"fid": fixture_id})
        if rows:
            conn.execute(insert(text('"Prediction"')), rows)
    return len(rows)


def load_thresholds() -> dict:
    from sqlalchemy import create_engine, text
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        row = conn.execute(text('SELECT thresholds FROM "Config" WHERE id = \'singleton\'')).first()
    if not row:
        return {
            "MATCH_RESULT": settings.threshold_match_result,
            "DOUBLE_CHANCE": settings.threshold_double_chance,
            "OTHER": settings.threshold_other,
            "COMBINATION": settings.threshold_combination,
        }
    return dict(row[0])
