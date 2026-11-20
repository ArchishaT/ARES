"""
Trains and evaluates four approaches to phishing URL detection:
rule-based, logistic regression, random forest, and a small MLP neural
network. Produces results.json consumed by the dashboard.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.generate_dataset import generate, make_legit_url, make_phishing_url  # noqa: E402
from features import FEATURE_NAMES, feature_vector  # noqa: E402
from models import rule_based  # noqa: E402

MODELS_DIR = ROOT / "models" / "artifacts"
MODELS_DIR.mkdir(exist_ok=True)


def build_dataset(n_per_class: int = 1500):
    rows = generate(n_per_class)
    urls = [r[0] for r in rows]
    labels = np.array([r[1] for r in rows])
    X = np.array([feature_vector(u) for u in urls])
    return urls, X, labels


def adversarial_evasion_url() -> str:
    """Crafts a HARDER phishing example that deliberately avoids the most
    obvious signals (no urgent keywords, no IP literal, uses HTTPS and a
    common .com TLD, shallow subdomain depth) -- a single-character
    typosquat of a brand's real domain. This is a much more meaningful
    robustness test than naively adding more suspicious tokens: it asks
    whether the detector generalizes past the surface patterns in the
    training distribution, or whether it just memorized "urgent keyword
    present" / "weird TLD" style shortcuts."""
    import random
    from data.generate_dataset import BRANDS

    brand = random.choice(BRANDS)
    typo_ops = [
        lambda b: b[:-1] + random.choice("abcdefghijklmnopqrstuvwxyz"),  # swap last letter
        lambda b: b.replace("o", "0", 1) if "o" in b else b + "1",
        lambda b: b[: len(b) // 2] + b[len(b) // 2] + b[len(b) // 2:],  # duplicate a middle char
        lambda b: b.replace("l", "1", 1) if "l" in b else b + "-online",
    ]
    typo_domain = random.choice(typo_ops)(brand)
    return f"https://{typo_domain}.com/account/dashboard"


def evaluate(name: str, y_true, y_pred, y_proba=None) -> dict:
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return {
        "model": name,
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "false_positive_rate": round(float(fpr), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def main():
    print("Generating dataset...")
    urls, X, y = build_dataset(1500)
    urls_train, urls_test, X_train, X_test, y_train, y_test = train_test_split(
        urls, X, y, test_size=0.25, random_state=42, stratify=y
    )

    scaler = StandardScaler().fit(X_train)
    X_train_s, X_test_s = scaler.transform(X_train), scaler.transform(X_test)

    results = []

    # -- Rule-based (no training) ------------------------------------------
    rb_pred = np.array([rule_based.predict(u) for u in urls_test])
    results.append(evaluate("rule_based", y_test, rb_pred))

    # -- Logistic Regression -------------------------------------------------
    lr = LogisticRegression(max_iter=1000).fit(X_train_s, y_train)
    lr_pred = lr.predict(X_test_s)
    results.append(evaluate("logistic_regression", y_test, lr_pred))
    joblib.dump(lr, MODELS_DIR / "logistic_regression.joblib")

    # -- Random Forest -----------------------------------------------------
    rf = RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42).fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    results.append(evaluate("random_forest", y_test, rf_pred))
    joblib.dump(rf, MODELS_DIR / "random_forest.joblib")

    # -- Neural Network (MLP) -------------------------------------------------
    mlp = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=500, random_state=42).fit(X_train_s, y_train)
    mlp_pred = mlp.predict(X_test_s)
    results.append(evaluate("neural_network", y_test, mlp_pred))
    joblib.dump(mlp, MODELS_DIR / "neural_network.joblib")

    joblib.dump(scaler, MODELS_DIR / "scaler.joblib")

    # -- Feature importance (for the explanation layer / dashboard) -----------
    feature_importance = {
        "logistic_regression": dict(zip(FEATURE_NAMES, [round(float(c), 4) for c in lr.coef_[0]])),
        "random_forest": dict(zip(FEATURE_NAMES, [round(float(c), 4) for c in rf.feature_importances_])),
    }

    # -- Robustness test: harder adversarial typosquat examples ---------------
    # These deliberately avoid the loud signals (urgent keywords, IP literals,
    # odd TLDs) the training distribution leans on, to test generalization
    # rather than memorized surface patterns.
    print("Running robustness evaluation on adversarial typosquat URLs...")
    obf_urls = [adversarial_evasion_url() for _ in range(300)]
    obf_X = np.array([feature_vector(u) for u in obf_urls])
    obf_X_s = scaler.transform(obf_X)
    obf_y = np.ones(len(obf_urls))

    robustness = {
        "rule_based": round(float(np.mean([rule_based.predict(u) for u in obf_urls])), 4),
        "logistic_regression": round(float(lr.score(obf_X_s, obf_y)), 4),
        "random_forest": round(float(rf.score(obf_X, obf_y)), 4),
        "neural_network": round(float(mlp.score(obf_X_s, obf_y)), 4),
    }
    print("Recall on obfuscated phishing URLs (robustness):", robustness)

    output = {
        "dataset_size": len(urls),
        "test_size": len(urls_test),
        "results": results,
        "feature_importance": feature_importance,
        "robustness_recall_on_obfuscated": robustness,
        "feature_names": FEATURE_NAMES,
    }
    with open(ROOT / "dashboard" / "results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(json.dumps(results, indent=2))
    print(f"\nSaved models to {MODELS_DIR}")
    print(f"Saved dashboard data to {ROOT / 'dashboard' / 'results.json'}")


if __name__ == "__main__":
    main()
