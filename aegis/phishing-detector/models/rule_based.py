"""
Rule-based baseline: a hand-tuned weighted sum over the same feature set
used by the ML models, thresholded to a binary decision. This exists as
the simplest possible baseline to compare the learned models against.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from features import FEATURE_NAMES, extract_features

WEIGHTS = {
    "url_length": 0.01,
    "num_dots": 0.3,
    "num_hyphens": 0.4,
    "num_digits": 0.05,
    "num_subdomains": 0.8,
    "has_ip_host": 3.0,
    "has_https": -1.0,
    "suspicious_tld": 2.5,
    "urgent_keyword_count": 1.2,
    "brand_in_subdomain_not_domain": 2.8,
    "path_entropy": 0.5,
    "has_at_symbol": 2.0,
    "has_suspicious_port": 1.5,
    "digit_letter_mix_in_domain": 1.0,
    "query_length": 0.02,
}
THRESHOLD = 3.0


def score(url: str) -> float:
    feats = extract_features(url)
    return sum(WEIGHTS[name] * feats[name] for name in FEATURE_NAMES)


def predict(url: str) -> int:
    return int(score(url) >= THRESHOLD)


def predict_proba(url: str) -> float:
    """Squash the raw weighted score into a pseudo-probability via a
    logistic function centered on the decision threshold, purely for
    comparability with the ML models' probability outputs."""
    import math
    s = score(url) - THRESHOLD
    return 1.0 / (1.0 + math.exp(-s))


def contributions(url: str) -> dict:
    feats = extract_features(url)
    return {name: WEIGHTS[name] * feats[name] for name in FEATURE_NAMES}
