"""Real-world phishing classifier evaluation against the OpenPhish live feed.

Pulls fresh phishing URLs from OpenPhish (no API key required), pairs them with
a list of well-known benign domains, runs both through the local /scan-url
endpoint, and writes a confusion matrix plus per-URL predictions CSV.

Designed for defense-day demonstration: proves the model generalises to URLs
seen for the first time outside the HuggingFace training distribution.

SAFETY: This script NEVER fetches the URLs, only sends them as strings to the
local classifier. Output is defanged before printing to stdout.

Usage:
    python scripts/eval_realworld.py
    python scripts/eval_realworld.py --sample 200 --endpoint http://localhost:8000
    python scripts/eval_realworld.py --no-cache  # force fresh OpenPhish pull
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import requests

OPENPHISH_FEED_URL = "https://openphish.com/feed.txt"
CACHE_TTL_HOURS = 1
DEFAULT_ENDPOINT = "http://localhost:8000"
DEFAULT_SAMPLE_SIZE = 200
DEFAULT_CONCURRENCY = 8

# Well-known benign domains (top global sites, mix of categories).
# Used as the "ham" class for confusion-matrix evaluation.
BENIGN_DOMAINS = [
    "https://www.google.com", "https://www.youtube.com", "https://www.facebook.com",
    "https://www.wikipedia.org", "https://www.amazon.com", "https://www.twitter.com",
    "https://www.instagram.com", "https://www.linkedin.com", "https://www.reddit.com",
    "https://www.github.com", "https://www.microsoft.com", "https://www.apple.com",
    "https://www.netflix.com", "https://www.spotify.com", "https://www.adobe.com",
    "https://www.dropbox.com", "https://www.paypal.com", "https://www.stripe.com",
    "https://www.shopify.com", "https://www.zoom.us", "https://www.slack.com",
    "https://www.notion.so", "https://www.figma.com", "https://www.canva.com",
    "https://www.medium.com", "https://www.stackoverflow.com", "https://www.quora.com",
    "https://www.cnn.com", "https://www.bbc.com", "https://www.nytimes.com",
    "https://www.theguardian.com", "https://www.reuters.com", "https://www.bloomberg.com",
    "https://www.imdb.com", "https://www.tripadvisor.com", "https://www.booking.com",
    "https://www.airbnb.com", "https://www.uber.com", "https://www.lyft.com",
    "https://www.tesla.com", "https://www.spacex.com", "https://www.nasa.gov",
    "https://www.harvard.edu", "https://www.mit.edu", "https://www.stanford.edu",
    "https://www.coursera.org", "https://www.udemy.com", "https://www.khanacademy.org",
    "https://www.duolingo.com", "https://www.npr.org", "https://www.ted.com",
    "https://www.openai.com", "https://www.anthropic.com", "https://www.huggingface.co",
    "https://www.kaggle.com", "https://www.gitlab.com", "https://www.bitbucket.org",
    "https://www.docker.com", "https://www.kubernetes.io", "https://www.python.org",
    "https://www.djangoproject.com", "https://www.flask.palletsprojects.com",
    "https://www.fastapi.tiangolo.com", "https://www.nodejs.org", "https://www.npmjs.com",
    "https://www.yarnpkg.com", "https://www.vercel.com", "https://www.netlify.com",
    "https://www.cloudflare.com", "https://www.digitalocean.com", "https://www.aws.amazon.com",
    "https://www.azure.microsoft.com", "https://cloud.google.com", "https://www.heroku.com",
    "https://www.mongodb.com", "https://www.postgresql.org", "https://www.redis.io",
    "https://www.elastic.co", "https://www.grafana.com", "https://www.prometheus.io",
    "https://www.terraform.io", "https://www.ansible.com", "https://www.jenkins.io",
]


@dataclass
class Prediction:
    url: str
    actual_label: str  # 'phishing' or 'benign'
    predicted_phishing: bool
    confidence: float
    phishing_type: str
    threat_level: str
    error: str = ""


def defang(url: str) -> str:
    """Make a URL safe to print/log so accidental clicks can't resolve it."""
    return url.replace("http://", "hxxp://").replace("https://", "hxxps://").replace(".", "[.]")


def cache_path() -> Path:
    cache_dir = Path(__file__).resolve().parent / ".cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / "openphish_feed.txt"


def fetch_openphish(use_cache: bool = True) -> list[str]:
    """Fetch the OpenPhish community feed, with a short local cache."""
    cache = cache_path()
    if use_cache and cache.exists():
        age = datetime.now() - datetime.fromtimestamp(cache.stat().st_mtime)
        if age < timedelta(hours=CACHE_TTL_HOURS):
            print(f"[cache] Using OpenPhish feed cached {age.seconds // 60} min ago")
            return [line for line in cache.read_text().splitlines() if line.startswith("http")]

    print(f"[fetch] Pulling fresh OpenPhish feed from {OPENPHISH_FEED_URL} ...")
    resp = requests.get(OPENPHISH_FEED_URL, timeout=15)
    resp.raise_for_status()
    cache.write_text(resp.text)
    urls = [line for line in resp.text.splitlines() if line.startswith("http")]
    print(f"[fetch] Got {len(urls)} live phishing URLs from OpenPhish")
    return urls


def scan_one(endpoint: str, url: str, actual_label: str, timeout: int = 30) -> Prediction:
    try:
        resp = requests.post(
            f"{endpoint}/scan-url",
            json={"url": url},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return Prediction(
            url=url,
            actual_label=actual_label,
            predicted_phishing=bool(data.get("is_phishing", False)),
            confidence=float(data.get("confidence", 0.0)),
            phishing_type=str(data.get("phishing_type", "")),
            threat_level=str(data.get("threat_level", "")),
        )
    except Exception as e:
        return Prediction(
            url=url,
            actual_label=actual_label,
            predicted_phishing=False,
            confidence=0.0,
            phishing_type="",
            threat_level="",
            error=str(e)[:200],
        )


def run_evaluation(
    endpoint: str,
    phishing_urls: list[str],
    benign_urls: list[str],
    concurrency: int,
) -> list[Prediction]:
    jobs: list[tuple[str, str]] = (
        [(u, "phishing") for u in phishing_urls]
        + [(u, "benign") for u in benign_urls]
    )
    results: list[Prediction] = []
    print(f"[scan] Submitting {len(jobs)} URLs to {endpoint} with concurrency={concurrency}")
    start = time.time()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(scan_one, endpoint, url, label) for url, label in jobs]
        for i, fut in enumerate(as_completed(futures), 1):
            results.append(fut.result())
            if i % 20 == 0 or i == len(jobs):
                print(f"  ... {i}/{len(jobs)} scanned ({time.time() - start:.1f}s elapsed)")
    return results


def compute_metrics(preds: list[Prediction]) -> dict:
    tp = sum(1 for p in preds if p.actual_label == "phishing" and p.predicted_phishing)
    fn = sum(1 for p in preds if p.actual_label == "phishing" and not p.predicted_phishing)
    fp = sum(1 for p in preds if p.actual_label == "benign" and p.predicted_phishing)
    tn = sum(1 for p in preds if p.actual_label == "benign" and not p.predicted_phishing)
    errors = sum(1 for p in preds if p.error)

    total = tp + fn + fp + tn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0

    return {
        "true_positive": tp,
        "false_negative": fn,
        "false_positive": fp,
        "true_negative": tn,
        "errors": errors,
        "total_scored": total,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
    }


def write_outputs(out_dir: Path, preds: list[Prediction], metrics: dict, meta: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    predictions_csv = out_dir / "predictions.csv"
    with predictions_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "actual_label", "predicted_phishing", "confidence",
            "phishing_type", "threat_level", "url_defanged", "error",
        ])
        for p in preds:
            w.writerow([
                p.actual_label, p.predicted_phishing, p.confidence,
                p.phishing_type, p.threat_level, defang(p.url), p.error,
            ])

    confusion_csv = out_dir / "confusion_matrix.csv"
    with confusion_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["", "predicted_phishing", "predicted_benign"])
        w.writerow([
            "actual_phishing",
            metrics["true_positive"],
            metrics["false_negative"],
        ])
        w.writerow([
            "actual_benign",
            metrics["false_positive"],
            metrics["true_negative"],
        ])

    summary_json = out_dir / "summary.json"
    summary_json.write_text(json.dumps({"meta": meta, "metrics": metrics}, indent=2))

    print(f"\n[output] {predictions_csv}")
    print(f"[output] {confusion_csv}")
    print(f"[output] {summary_json}")


def print_report(metrics: dict, meta: dict) -> None:
    print("\n" + "=" * 60)
    print("  REAL-WORLD PHISHING EVAL — SUMMARY")
    print("=" * 60)
    print(f"  Endpoint:           {meta['endpoint']}")
    print(f"  Phishing source:    OpenPhish live feed")
    print(f"  Sample size:        {meta['phishing_count']} phish + {meta['benign_count']} benign")
    print(f"  Timestamp:          {meta['timestamp']}")
    print("-" * 60)
    print(f"  Accuracy:           {metrics['accuracy']:.4f}")
    print(f"  Precision (phish):  {metrics['precision']:.4f}")
    print(f"  Recall (phish):     {metrics['recall']:.4f}")
    print(f"  F1:                 {metrics['f1']:.4f}")
    print(f"  False-positive rate:{metrics['false_positive_rate']:.4f}")
    print("-" * 60)
    print("  Confusion matrix:")
    print(f"                  pred_phish  pred_benign")
    print(f"    actual_phish   {metrics['true_positive']:>6}      {metrics['false_negative']:>6}")
    print(f"    actual_benign  {metrics['false_positive']:>6}      {metrics['true_negative']:>6}")
    if metrics["errors"]:
        print(f"  Errored requests:   {metrics['errors']}")
    print("=" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT,
                        help=f"ML service base URL (default: {DEFAULT_ENDPOINT})")
    parser.add_argument("--sample", type=int, default=DEFAULT_SAMPLE_SIZE,
                        help=f"Phishing URLs to sample from OpenPhish (default: {DEFAULT_SAMPLE_SIZE})")
    parser.add_argument("--benign-sample", type=int, default=None,
                        help="Benign URLs to use (default: all hardcoded ~80)")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                        help=f"Parallel requests (default: {DEFAULT_CONCURRENCY})")
    parser.add_argument("--no-cache", action="store_true",
                        help="Force a fresh OpenPhish feed pull")
    parser.add_argument("--out", default=None,
                        help="Output directory (default: app/model/evaluations/realworld_<timestamp>)")
    args = parser.parse_args()

    try:
        phish_urls = fetch_openphish(use_cache=not args.no_cache)
    except requests.RequestException as e:
        print(f"[error] Failed to fetch OpenPhish feed: {e}", file=sys.stderr)
        return 1

    if not phish_urls:
        print("[error] OpenPhish feed was empty", file=sys.stderr)
        return 1

    phish_sample = phish_urls[: args.sample]
    benign_sample = BENIGN_DOMAINS[: args.benign_sample] if args.benign_sample else BENIGN_DOMAINS

    preds = run_evaluation(args.endpoint, phish_sample, benign_sample, args.concurrency)
    metrics = compute_metrics(preds)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out) if args.out else (
        Path(__file__).resolve().parent.parent / "app" / "model" / "evaluations" / f"realworld_{timestamp}"
    )
    meta = {
        "endpoint": args.endpoint,
        "phishing_source": "OpenPhish (https://openphish.com/feed.txt)",
        "phishing_count": len(phish_sample),
        "benign_count": len(benign_sample),
        "concurrency": args.concurrency,
        "timestamp": datetime.now().isoformat(),
    }

    write_outputs(out_dir, preds, metrics, meta)
    print_report(metrics, meta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
