from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    db_path: Path = Path(os.environ.get("DB_PATH", "./data/app.db"))
    claude_api_key: str = os.environ.get("CLAUDE_API_KEY", "")
    anthropic_model: str = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    default_webhook_url: str = os.environ.get("DEFAULT_WEBHOOK_URL", "")
    max_text_chars: int = int(os.environ.get("MAX_TEXT_CHARS", "12000"))
    max_images: int = int(os.environ.get("MAX_IMAGES", "8"))
    max_image_bytes: int = int(os.environ.get("MAX_IMAGE_BYTES", str(2 * 1024 * 1024)))
    auto_min_text_lines: int = int(os.environ.get("AUTO_MIN_TEXT_LINES", "5"))
    webhook_max_retries: int = int(os.environ.get("WEBHOOK_MAX_RETRIES", "3"))
    webhook_backoff_seconds: float = float(os.environ.get("WEBHOOK_BACKOFF_SECONDS", "1.5"))


SETTINGS = Settings()
