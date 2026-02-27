from __future__ import annotations

from typing import Any, Dict

from app.config import SETTINGS
from dynamic.scrape import scrape_page_sync
from static.scrape import scrape_static


def scrape_url(url: str, mode: str) -> Dict[str, Any]:
    if mode == "static":
        return scrape_static(url)
    if mode == "dynamic":
        return scrape_page_sync(url)

    static_data = scrape_static(url)
    text_lines = static_data.get("text") or []
    images = static_data.get("images") or []
    if len(text_lines) >= SETTINGS.auto_min_text_lines or images:
        return static_data
    return scrape_page_sync(url)
