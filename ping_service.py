"""
ping_service.py
---------------
Keep-alive & monitoring script for ML-ETA HuggingFace Space.

Behaviour:
  1. GET /            → primary health check (returns online status)
  2. GET /model-info  → warm-up request so the Space is fully ready
  3. Append result to ping_log.csv
  4. Send status to Discord webhook if configured

Environment variables (set as GitHub Secrets):
  HF_SPACE_URL          - base URL of the HF Space (no trailing slash)
                          e.g. https://username-ml-eta.hf.space
  DISCORD_WEBHOOK_URL   - Discord incoming webhook URL (optional)
"""

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load environment variables from .env file (if running locally)
load_dotenv()

# Fix Windows cp1252 Unicode encoding issue
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
BASE_URL: str = os.environ.get("HF_SPACE_URL", "").rstrip("/")
DISCORD_WEBHOOK: str = os.environ.get("DISCORD_WEBHOOK_URL", "")

TIMEOUT_SECONDS: int = 60
LOG_FILE: Path = Path("ping_log.csv")
LOG_FIELDNAMES = ["timestamp", "status_code", "response_time_ms", "status"]

# Helpers
def utc_now() -> str:
    """Return current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_log_header() -> None:
    """Create CSV file with header row if it doesn't exist yet."""
    if not LOG_FILE.exists():
        with LOG_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=LOG_FIELDNAMES)
            writer.writeheader()


def append_log(timestamp: str, status_code: int | str, response_time_ms: float | str, status: str) -> None:
    """Append a single row to the ping log CSV."""
    ensure_log_header()
    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDNAMES)
        writer.writerow({
            "timestamp": timestamp,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "status": status,
        })


def send_discord_message(title: str, message: str, is_success: bool = False) -> None:
    """Send a message to Discord webhook."""
    if not DISCORD_WEBHOOK:
        print("[WARN] DISCORD_WEBHOOK_URL is not set — skipping Discord message.")
        return

    color = 0x27AE60 if is_success else 0xE74C3C  # green or red

    payload = {
        "username": "ML-ETA Space Monitor",
        "avatar_url": "https://huggingface.co/front/assets/huggingface_logo-noborder.svg",
        "embeds": [
            {
                "title": title,
                "description": message,
                "color": color,
                "footer": {"text": f"Checked at {utc_now()} UTC"},
            }
        ],
    }

    try:
        resp = requests.post(
            DISCORD_WEBHOOK,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        if resp.status_code in (200, 204):
            print("[INFO] Discord message sent successfully.")
        else:
            print(f"[WARN] Discord webhook returned {resp.status_code}: {resp.text}")
    except requests.RequestException as exc:
        print(f"[ERROR] Failed to send Discord message: {exc}")


def send_discord_alert(message: str) -> None:
    """Send an error alert message to Discord."""
    send_discord_message("🚨 ML-ETA Space — Health Check Failed", message, is_success=False)


# Core ping logic
def ping_health() -> tuple[bool, int | str, float]:
    """
    GET / and return (success, status_code, response_time_ms).
    success is True only when HTTP 200 is received.
    """
    url = f"{BASE_URL}/"
    print(f"[INFO] Pinging health endpoint: {url}")

    try:
        resp = requests.get(url, timeout=TIMEOUT_SECONDS)
        elapsed_ms = round(resp.elapsed.total_seconds() * 1000, 2)
        print(f"[INFO] / -> {resp.status_code} ({elapsed_ms} ms)")
        return resp.status_code == 200, resp.status_code, elapsed_ms

    except requests.Timeout:
        print(f"[ERROR] / request timed out after {TIMEOUT_SECONDS}s")
        return False, "TIMEOUT", TIMEOUT_SECONDS * 1000

    except requests.RequestException as exc:
        print(f"[ERROR] / request failed: {exc}")
        return False, "ERROR", 0.0


def warm_up() -> None:
    """
    GET /model-info to warm up the LightGBM model.
    Failures here are logged but do NOT trigger a Discord alert.
    """
    url = f"{BASE_URL}/model-info"
    print(f"[INFO] Sending warm-up request: {url}")

    try:
        resp = requests.get(url, timeout=TIMEOUT_SECONDS)
        elapsed_ms = round(resp.elapsed.total_seconds() * 1000, 2)
        print(f"[INFO] /model-info (warm-up) → {resp.status_code} ({elapsed_ms} ms)")
    except requests.RequestException as exc:
        print(f"[WARN] Warm-up request failed (non-critical): {exc}")


# Entry point
def main() -> None:
    if not BASE_URL:
        print("[FATAL] HF_SPACE_URL environment variable is not set. Aborting.")
        sys.exit(1)

    print("=" * 60)
    print(f"  ML-ETA Keep-Alive Ping  |  {utc_now()}")
    print("=" * 60)

    timestamp = utc_now()

    # 1. Primary health check
    success, status_code, response_time_ms = ping_health()

    # 2. Determine log status label
    if success:
        status_label = "OK"
        print("[INFO] Health check PASSED ✅")
        success_msg = (
            f"**Endpoint:** `{BASE_URL}/`\n"
            f"**Status code:** `200`\n"
            f"**Response time:** `{response_time_ms} ms`\n"
            f"**Time:** `{timestamp} UTC`\n\n"
            "ML-ETA Space is healthy and operational! 🚌💨"
        )
        send_discord_message("✅ ML-ETA Space — Health Check Passed", success_msg, is_success=True)
    else:
        status_label = "FAIL"
        print("[WARN] Health check FAILED ❌")
        alert_msg = (
            f"**Endpoint:** `{BASE_URL}/`\n"
            f"**Status code:** `{status_code}`\n"
            f"**Response time:** `{response_time_ms} ms`\n"
            f"**Time:** `{timestamp} UTC`\n\n"
            "Please check the HuggingFace Space logs immediately."
        )
        send_discord_alert(alert_msg)

    # 3. Append result to CSV log
    append_log(timestamp, status_code, response_time_ms, status_label)
    print(f"[INFO] Result appended to {LOG_FILE}")

    # 4. Warm-up request (always run)
    warm_up()

    print("=" * 60)
    print("  Ping complete.")
    print("=" * 60)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
