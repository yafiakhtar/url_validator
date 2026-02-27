from __future__ import annotations

import time
from typing import Any, Dict

import httpx

from app.config import SETTINGS


def send_webhook(webhook_url: str, payload: Dict[str, Any]) -> None:
    attempt = 0
    while True:
        attempt += 1
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(webhook_url, json=payload)
                resp.raise_for_status()
                return
        except httpx.HTTPError:
            if attempt >= SETTINGS.webhook_max_retries:
                raise
            time.sleep(SETTINGS.webhook_backoff_seconds * attempt)
