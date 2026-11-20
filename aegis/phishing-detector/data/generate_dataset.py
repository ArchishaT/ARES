"""
Generates a synthetic dataset of phishing-style and legitimate-style
URLs for training/evaluating the detector.

No real phishing URLs are scraped or distributed here. Phishing-style
examples are procedurally generated using well-documented structural
patterns real phishing campaigns are known to use (IP-literal hosts,
brand-name lookalike subdomains, excessive subdomain depth, suspicious
TLDs, URL-encoded obfuscation, keyword stuffing) -- the same approach
used by academic phishing-detection datasets that avoid redistributing
live malicious URLs.
"""
from __future__ import annotations

import csv
import random
import string
from pathlib import Path

random.seed(42)

BRANDS = ["paypal", "amazon", "apple", "microsoft", "netflix", "chase", "wellsfargo", "google", "facebook", "irs"]
LEGIT_DOMAINS = [
    "github.com", "wikipedia.org", "nytimes.com", "stackoverflow.com", "python.org",
    "mozilla.org", "arxiv.org", "nature.com", "bbc.co.uk", "harvard.edu",
    "apple.com", "amazon.com", "paypal.com", "microsoft.com", "netflix.com",
]
SUSPICIOUS_TLDS = [".top", ".xyz", ".tk", ".click", ".gq", ".cf", ".ml", ".work", ".support", ".verify"]
URGENT_WORDS = ["verify", "secure", "update", "confirm", "login", "account", "suspended", "alert", "billing", "unlock"]


def _rand_str(n: int) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def make_legit_url() -> str:
    domain = random.choice(LEGIT_DOMAINS)
    path_depth = random.randint(0, 3)
    path = "/".join(_rand_str(random.randint(3, 8)) for _ in range(path_depth))
    scheme = "https"
    sub = random.choice(["", "www.", "docs.", "blog."])
    return f"{scheme}://{sub}{domain}/{path}".rstrip("/")


def make_phishing_url() -> str:
    pattern = random.choice(["ip_literal", "lookalike_subdomain", "deep_subdomain", "suspicious_tld", "keyword_stuff", "homoglyph"])
    brand = random.choice(BRANDS)

    if pattern == "ip_literal":
        ip = ".".join(str(random.randint(1, 255)) for _ in range(4))
        return f"http://{ip}/{brand}-{random.choice(URGENT_WORDS)}/login.php"

    if pattern == "lookalike_subdomain":
        return f"http://{brand}-{random.choice(URGENT_WORDS)}.{_rand_str(6)}.com/secure"

    if pattern == "deep_subdomain":
        depth = random.randint(3, 6)
        subs = ".".join(_rand_str(5) for _ in range(depth))
        return f"http://{subs}.{brand}.{_rand_str(4)}.com/verify"

    if pattern == "suspicious_tld":
        tld = random.choice(SUSPICIOUS_TLDS)
        return f"http://{brand}{_rand_str(4)}{tld}/{random.choice(URGENT_WORDS)}"

    if pattern == "keyword_stuff":
        words = "-".join(random.sample(URGENT_WORDS, 3))
        return f"http://{brand}-{words}.{_rand_str(5)}.net/account/update.php?id={_rand_str(10)}"

    # homoglyph: zero-for-o, rn-for-m style substitutions (visually similar chars)
    swapped = brand.replace("o", "0").replace("a", "4").replace("e", "3")
    return f"http://{swapped}.{_rand_str(4)}-{random.choice(URGENT_WORDS)}.com/login"


def generate(n_per_class: int = 1500) -> list[tuple[str, int]]:
    rows = [(make_legit_url(), 0) for _ in range(n_per_class)]
    rows += [(make_phishing_url(), 1) for _ in range(n_per_class)]
    random.shuffle(rows)
    return rows


def write_csv(path: str, rows: list[tuple[str, int]]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "label"])
        writer.writerows(rows)


if __name__ == "__main__":
    rows = generate(1500)
    out = Path(__file__).parent / "urls.csv"
    write_csv(str(out), rows)
    print(f"Wrote {len(rows)} rows to {out}")
