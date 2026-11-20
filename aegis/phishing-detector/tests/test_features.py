import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from features import extract_features
from models import rule_based


def test_ip_host_detected():
    feats = extract_features("http://192.168.1.5/login")
    assert feats["has_ip_host"] == 1


def test_https_detected():
    feats = extract_features("https://example.com")
    assert feats["has_https"] == 1
    feats2 = extract_features("http://example.com")
    assert feats2["has_https"] == 0


def test_suspicious_tld_detected():
    feats = extract_features("http://secure-login.top/account")
    assert feats["suspicious_tld"] == 1


def test_urgent_keywords_counted():
    feats = extract_features("http://verify-account-login.com/confirm")
    assert feats["urgent_keyword_count"] >= 2


def test_rule_based_flags_obvious_phishing():
    url = "http://1.2.3.4/paypal-verify-login/secure.php"
    assert rule_based.predict(url) == 1


def test_rule_based_passes_clean_legit_url():
    url = "https://docs.python.org/3/tutorial/index.html"
    assert rule_based.predict(url) == 0


def test_subdomain_depth_counted():
    feats = extract_features("http://a.b.c.d.example.com/path")
    assert feats["num_subdomains"] >= 2
