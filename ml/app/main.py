"""FastAPI entrypoint for the ML service.

Endpoints:
  GET  /health            -> comprehensive system health check
  POST /sync/competitions -> pull competitions/teams/standings (DataManager)
  POST /sync/elo          -> sync ClubElo ratings
  POST /sync/kaggle       -> import + persist historical Kaggle datasets
  POST /train             -> train a model from historical data
  POST /predict           -> generate predictions for a fixture
  GET  /providers         -> provider connection status
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .engine import Threshold, derive_markets, derive_combinations, qualify_and_rank
from . import db
from . import scheduler
from .data_manager import data_manager

from . import db
from .db import DbDataProvider
from . import training
from .feature_pipeline import build_matrix
from .feature_store import FeatureStore
from .persistence import persist_predictions, load_thresholds
from .pipeline import build_features, predict_1x2
from .training import load_model

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("ml-service")

TOP_COMPETITIONS = ["English Premier League", "La Liga", "Bundesliga",
                    "Serie A", "Ligue 1", "UEFA Champions League"]


class PredictRequest(BaseModel):
    fixtureId: str


class TrainRequest(BaseModel):
    modelName: str = "gradient_boosting"
    competitions: list = TOP_COMPETITIONS


class SyncRequest(BaseModel):
    competitions: list = TOP_COMPETITIONS


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.model_dir, exist_ok=True)
    try:
        db.init_db()
    except Exception as exc:
        logger.warning("DB init skipped (database unavailable): %s", exc)
    scheduler.start()
    yield
    scheduler.stop()


app = FastAPI(title="Match Predictor ML Service", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return scheduler.health_check()


@app.get("/providers")
def providers():
    return {"providers": data_manager.provider_status()}


@app.post("/sync/competitions")
def sync_competitions(req: SyncRequest, background: BackgroundTasks):
    background.add_task(scheduler.run_sync_competitions, req.competitions)
    return {"status": "queued", "competitions": req.competitions}


@app.post("/sync/elo")
def sync_elo(background: BackgroundTasks):
    background.add_task(scheduler.run_sync_elo)
    return {"status": "queued"}


@app.post("/sync/kaggle")
def sync_kaggle(req: SyncRequest, background: BackgroundTasks):
    background.add_task(scheduler.run_import_kaggle, req.competitions)
    return {"status": "queued"}


@app.post("/train")
def train_model(req: TrainRequest):
    return scheduler.run_train(req.modelName, req.competitions)


@app.post("/predict")
def predict(req: PredictRequest):
    provider = DbDataProvider(settings.database_url)
    features, meta = build_features(provider, req.fixtureId)
    model = load_model()
    home, draw, away = predict_1x2(model, features)

    base = derive_markets(home, draw, away, meta)
    combos = derive_combinations(base)
    all_preds = base + combos

    thr = load_thresholds()
    thresholds = Threshold(
        MATCH_RESULT=thr["MATCH_RESULT"],
        DOUBLE_CHANCE=thr["DOUBLE_CHANCE"],
        OTHER=thr["OTHER"],
        COMBINATION=thr["COMBINATION"],
    )
    qualified = qualify_and_rank(all_preds, thresholds)
    persist_predictions(req.fixtureId, all_preds, "v2")
    return {
        "fixtureId": req.fixtureId,
        "modelVersion": "v2",
        "baseProbabilities": {"HOME": home, "DRAW": draw, "AWAY": away},
        "predictions": [
            {
                "market": p.market,
                "selection": p.selection,
                "probability": round(p.probability, 4),
                "confidence": round(p.confidence, 2),
                "expectedValue": round(p.expected_value, 4) if p.expected_value is not None else None,
                "status": p.status,
                "reasons": p.reasons,
            }
            for p in all_preds
        ],
    }
