"""
Feature extraction for URL-based phishing detection.

All features are computed purely from the URL string (structure, lexical
patterns) -- no live network requests, no WHOIS lookups. "Domain age" is
therefore modeled as a lexical proxy (presence of random-looking,
high-entropy subdomains tends to correlate with freshly-registered
throwaway domains) rather than a real registration-date lookup, since
this project intentionally avoids querying any live external service.
"""
from __future__ import annotations

import math
import re
from urllib.parse import urlparse

SUSPICIOUS_TLDS = {"top", "xyz", "tk", "click", "gq", "cf", "ml", "work", "support", "verify"}
URGENT_WORDS = {"verify", "secure", "update", "confirm", "login", "account", "suspended", "alert", "billing", "unlock"}
BRANDS = {"paypal", "amazon", "apple", "microsoft", "netflix", "chase", "wellsfargo", "google", "facebook", "irs"}

FEATURE_NAMES = [
    "url_length",
    "num_dots",
    "num_hyphens",
    "num_digits",
    "num_subdomains",
    "has_ip_host",
    "has_https",
    "suspicious_tld",
    "urgent_keyword_count",
    "brand_in_subdomain_not_domain",
    "path_entropy",
    "has_at_symbol",
    "has_suspicious_port",
    "digit_letter_mix_in_domain",
    "query_length",
]


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    probs = [s.count(c) / len(s) for c in set(s)]
    return round(-sum(p * math.log2(p) for p in probs), 3)


def _is_ip(host: str) -> bool:
    return bool(re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", host))


def extract_features(url: str) -> dict:
    url = url.strip()
    parsed = urlparse(url if "://" in url else f"http://{url}")
    host = parsed.hostname or ""
    parts = host.split(".") if host else []

    registrable = ".".join(parts[-2:]) if len(parts) >= 2 else host
    subdomains = parts[:-2] if len(parts) > 2 else []
    tld = parts[-1] if parts else ""

    brand_in_sub = any(b in ".".join(subdomains) for b in BRANDS)
    brand_in_domain = any(b in registrable for b in BRANDS)

    feats = {
        "url_length": len(url),
        "num_dots": host.count("."),
        "num_hyphens": url.count("-"),
        "num_digits": sum(c.isdigit() for c in url),
        "num_subdomains": max(0, len(parts) - 2),
        "has_ip_host": int(_is_ip(host)),
        "has_https": int(parsed.scheme == "https"),
        "suspicious_tld": int(tld in SUSPICIOUS_TLDS),
        "urgent_keyword_count": sum(1 for w in URGENT_WORDS if w in url.lower()),
        "brand_in_subdomain_not_domain": int(brand_in_sub and not brand_in_domain),
        "path_entropy": _shannon_entropy(parsed.path),
        "has_at_symbol": int("@" in url),
        "has_suspicious_port": int(parsed.port is not None and parsed.port not in (80, 443)),
        "digit_letter_mix_in_domain": int(bool(re.search(r"[a-z]\d|\d[a-z]", registrable))),
        "query_length": len(parsed.query or ""),
    }
    return feats


def feature_vector(url: str) -> list[float]:
    feats = extract_features(url)
    return [float(feats[name]) for name in FEATURE_NAMES]


# Domain-knowledge direction for each feature, independent of any
# individual model's (sometimes unsigned, e.g. Random Forest / MLP)
# internal contribution scores. "higher" = larger values raise risk;
# "present" = risk is raised only when the binary flag is 1 (and the
# feature says nothing when it's 0); "absent" = risk is raised when the
# flag is 0 (currently only HTTPS presence, where missing HTTPS is the
# risk signal).
_DIRECTION = {
    "url_length": "higher", "num_dots": "higher", "num_hyphens": "higher", "num_digits": "higher",
    "num_subdomains": "higher", "has_ip_host": "present", "has_https": "absent",
    "suspicious_tld": "present", "urgent_keyword_count": "higher",
    "brand_in_subdomain_not_domain": "present", "path_entropy": "higher", "has_at_symbol": "present",
    "has_suspicious_port": "present", "digit_letter_mix_in_domain": "present", "query_length": "higher",
}

_READABLE = {
    "url_length": "unusually long URL",
    "num_dots": "unusual number of domain segments",
    "num_hyphens": "excessive hyphens in the domain/path",
    "num_digits": "unusually high digit count",
    "num_subdomains": "excessive subdomain depth",
    "has_ip_host": "raw IP address used instead of a domain name",
    "has_https": "missing HTTPS encryption",
    "suspicious_tld": "uncommon/high-risk top-level domain",
    "urgent_keyword_count": "urgency/credential-harvesting keywords in the URL",
    "brand_in_subdomain_not_domain": "brand name used as a subdomain rather than the real domain",
    "path_entropy": "high-entropy (random-looking) URL path",
    "has_at_symbol": "'@' symbol used to obscure the true destination",
    "has_suspicious_port": "non-standard port number",
    "digit_letter_mix_in_domain": "letter/digit substitution pattern in the domain (possible homoglyph)",
    "query_length": "unusually long query string",
}


def explain_prediction(url: str, contributions: dict[str, float], top_k: int = 4) -> list[str]:
    """Ranks features by the model's contribution magnitude (how much
    each feature mattered to this specific decision), but determines the
    risk DIRECTION from fixed domain knowledge rather than the model's
    raw contribution sign -- Random Forest / MLP contribution proxies
    used elsewhere in this project are magnitude-only and not reliably
    signed, so deriving "increases/decreases risk" from them directly
    would misreport protective features (e.g. HTTPS) as risk-increasing."""
    feats = extract_features(url)
    ranked = sorted(contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)
    out = []
    for name, _ in ranked:
        value = feats.get(name, 0)
        kind = _DIRECTION.get(name, "higher")

        if kind == "present" and value == 0:
            continue  # flag not set: not a meaningful signal either way
        if kind == "higher" and value == 0:
            continue  # zero count: nothing to report

        increases = (kind in ("present", "higher")) or (kind == "absent" and value == 0)
        direction = "increases" if increases else "decreases"
        out.append(f"{_READABLE.get(name, name)} ({direction} risk; value={value})")
        if len(out) >= top_k:
            break
    return out
