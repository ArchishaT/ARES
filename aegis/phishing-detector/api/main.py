"""
Inference API for the phishing detector. Serves predictions from any of
the four trained approaches plus a plain-English explanation of which
URL features drove the decision.

Run with: uvicorn api.main:app --port 8010 (from the phishing-detector/ dir)
"""
from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from features import FEATURE_NAMES, extract_features, explain_prediction, feature_vector  # noqa: E402
from models import rule_based  # noqa: E402

MODELS_DIR = ROOT / "models" / "artifacts"

app = FastAPI(title="Phishing Detector API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_cache: dict = {}


def _load():
    if not _cache:
        try:
            _cache["scaler"] = joblib.load(MODELS_DIR / "scaler.joblib")
            _cache["lr"] = joblib.load(MODELS_DIR / "logistic_regression.joblib")
            _cache["rf"] = joblib.load(MODELS_DIR / "random_forest.joblib")
            _cache["mlp"] = joblib.load(MODELS_DIR / "neural_network.joblib")
        except FileNotFoundError:
            pass
    return _cache


class PredictRequest(BaseModel):
    url: str
    model: str = "random_forest"  # rule_based | logistic_regression | random_forest | neural_network


class PredictResponse(BaseModel):
    url: str
    model: str
    is_phishing: bool
    probability: float
    explanation: list[str]
    features: dict


@app.get("/")
def root():
    return {"name": "Phishing Detector API", "status": "online", "models_loaded": bool(_load())}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    url = req.url
    feats = extract_features(url)

    if req.model == "rule_based":
        proba = rule_based.predict_proba(url)
        is_phish = bool(rule_based.predict(url))
        contributions = rule_based.contributions(url)
        explanation = explain_prediction(url, contributions)
        return PredictResponse(url=url, model=req.model, is_phishing=is_phish, probability=round(proba, 4),
                                explanation=explanation, features=feats)

    cache = _load()
    if req.model not in ("logistic_regression", "random_forest", "neural_network") or not cache:
        raise HTTPException(400, "Model not available. Run models/train.py first, or request model='rule_based'.")

    x = np.array([feature_vector(url)])
    key = {"logistic_regression": "lr", "random_forest": "rf", "neural_network": "mlp"}[req.model]
    model = cache[key]

    if req.model == "random_forest":
        proba = float(model.predict_proba(x)[0][1])
        contributions = dict(zip(FEATURE_NAMES, model.feature_importances_ * (np.array(feature_vector(url)) > 0)))
    else:
        x_s = cache["scaler"].transform(x)
        proba = float(model.predict_proba(x_s)[0][1])
        if req.model == "logistic_regression":
            contributions = dict(zip(FEATURE_NAMES, model.coef_[0] * x_s[0]))
        else:
            # MLP has no direct per-feature weight; approximate contribution
            # via first-layer weight magnitude times the (scaled) input.
            w1 = model.coefs_[0]  # shape (n_features, n_hidden)
            approx = np.abs(w1).mean(axis=1) * x_s[0]
            contributions = dict(zip(FEATURE_NAMES, approx))

    is_phish = proba >= 0.5
    explanation = explain_prediction(url, contributions)
    return PredictResponse(url=url, model=req.model, is_phishing=is_phish, probability=round(proba, 4),
                            explanation=explanation, features=feats)


@app.get("/models")
def list_models():
    cache = _load()
    return {
        "available": ["rule_based"] + ([k for k in ("logistic_regression", "random_forest", "neural_network") if cache]),
        "trained": bool(cache),
    }
