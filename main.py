"""FastAPI service exposing the IMDB sentiment classifier."""

from pathlib import Path
from typing import Literal

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

MODEL_PATH = Path("model/imdb_clf.joblib")

SERVICE_NAME = "imdb-sentiment-api"
SERVICE_VERSION = "0.1.0"

LABELS = {0: "negative", 1: "positive"}

app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION)

# Loaded on first use and reused after that. Not process-safe across workers;
# each worker process keeps its own cache and pays the load once.
_model: object | None = None


class ReviewIn(BaseModel):
    review: str = Field(min_length=1, description="A single movie review.")

    @field_validator("review")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("review must not be blank")
        return value


class PredictionOut(BaseModel):
    label: Literal["positive", "negative"]
    prediction: int
    confidence: float


def get_model():
    """Return the cached pipeline, loading it from disk on first call."""
    global _model
    if _model is None:
        try:
            _model = joblib.load(MODEL_PATH)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Model not found at {MODEL_PATH}. Run notebook.py to train it.",
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to load model from {MODEL_PATH}: {exc}",
            ) from exc
    return _model


def _predict_one(model, review: str) -> tuple[int, float]:
    prediction = int(model.predict([review])[0])
    confidence = float(max(model.predict_proba([review])[0]))
    return prediction, confidence


@app.get("/")
def read_root() -> dict:
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "model_path": str(MODEL_PATH),
    }


@app.get("/health")
def read_health() -> dict:
    return {"status": "ok", "model_loaded": _model is not None}


@app.post("/predict", response_model=PredictionOut)
def predict(payload: ReviewIn) -> PredictionOut:
    model = get_model()
    prediction, confidence = _predict_one(model, payload.review)
    return PredictionOut(
        label=LABELS[prediction],
        prediction=prediction,
        confidence=round(confidence, 4),
    )
