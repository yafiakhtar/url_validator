from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import List


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def content_hash(text_lines: List[str], image_urls: List[str]) -> str:
    hasher = hashlib.sha256()
    for line in text_lines:
        hasher.update(line.encode("utf-8", errors="ignore"))
        hasher.update(b"\n")
    for url in image_urls:
        hasher.update(url.encode("utf-8", errors="ignore"))
        hasher.update(b"\n")
    return hasher.hexdigest()
