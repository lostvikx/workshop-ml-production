"""FastAPI service exposing the IMDB sentiment classifier.

Run from the repository root: ``uv run fastapi dev main.py``.

Only ``model.predict`` is imported. ``model.train`` reads the 64 MB dataset at
module level, so importing it here would cost seconds and a large allocation on
every worker start.
"""

from pathlib import Path
from typing import Literal

import joblib
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

# `model.predict` is a namespace-package import and resolves against the
# directory the server was launched from.
from model.predict import load_model, predict_sentiment

MODEL_PATH = Path("model/imdb_clf.joblib")

APP_DIR = Path(__file__).parent / "app"

SERVICE_NAME = "imdb-sentiment-api"
SERVICE_VERSION = "0.1.0"

TRAIN_COMMAND = "uv run model/train.py"

app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION)

# Loaded on first use and reused after that. Not process-safe across workers;
# each worker process keeps its own cache and pays the load once.
_model = None


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
    label: Literal["Positive", "Negative"]
    prediction: int
    confidence: float


def get_model():
    """Return the cached pipeline, loading it from disk on first call."""
    global _model
    if _model is None:
        try:
            _model = load_model(MODEL_PATH)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Model not found at {MODEL_PATH}. Run `{TRAIN_COMMAND}` to train it.",
            ) from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to load model from {MODEL_PATH}: {exc}",
            ) from exc
    return _model


@app.get("/info")
def read_info() -> dict:
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
    result = predict_sentiment(payload.review, get_model())
    return PredictionOut(
        label=result["label"],
        prediction=result["prediction"],
        confidence=round(result["confidence"], 4),
    )


# Mounted last so the API routes above win the match. Serves app/index.html
# at /.
app.mount("/", StaticFiles(directory=APP_DIR, html=True), name="ui")
