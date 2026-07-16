"""FastAPI entrypoint for the ML service."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .engine import Threshold, derive_markets, derive_combinations, qualify_and_rank
from .pipeline import build_features, predict_1x2, load_model, train
from .persistence import persist_predictions, load_thresholds
from .providers import DbDataProvider


class PredictRequest(BaseModel):
    fixtureId: str


class TrainRequest(BaseModel):
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.model_dir, exist_ok=True)
    yield


import os

app = FastAPI(title="Match Predictor ML Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/train")
def train_model(_: TrainRequest = None):
    result = train()
    return result


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

    model_version = "v1"
    persist_predictions(req.fixtureId, all_preds, model_version)

    return {
        "fixtureId": req.fixtureId,
        "modelVersion": model_version,
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
