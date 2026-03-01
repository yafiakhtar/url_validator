from __future__ import annotations

import base64
import json
from typing import Any, Dict, List, Tuple

import httpx
import anthropic

from app.config import SETTINGS

SUPPORTED_MEDIA_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}


def _truncate_text(lines: List[str]) -> str:
    text = "\n".join(lines)
    if len(text) <= SETTINGS.max_text_chars:
        return text
    return text[: SETTINGS.max_text_chars]


def _fetch_image(url: str) -> Tuple[str, str] | None:
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            media_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
            if media_type not in SUPPORTED_MEDIA_TYPES:
                return None
            if len(resp.content) > SETTINGS.max_image_bytes:
                return None
            encoded = base64.b64encode(resp.content).decode("ascii")
            return media_type, encoded
    except httpx.HTTPError:
        return None


def _collect_images(image_urls: List[str]) -> List[Dict[str, Any]]:
    images: List[Dict[str, Any]] = []
    for url in image_urls[: SETTINGS.max_images]:
        result = _fetch_image(url)
        if not result:
            continue
        media_type, encoded = result
        images.append(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": encoded},
            }
        )
    return images


def _build_prompt(url: str, text: str, image_urls: List[str]) -> str:
    return (
        "You are a content safety analyst. First infer the website context (e.g., portfolio, "
        "e-commerce, news, documentation, hobby, research, community). Then assess risk ONLY "
        "if the content is promotional, instructional, transactional, or directly depicting "
        "harmful items. Do NOT flag neutral mentions in academic, historical, portfolio, or "
        "news contexts unless there is clear promotion or instruction.\n\n"
        "Return ONLY valid JSON with keys:\n"
        "- site_context: short string\n"
        "- risk_level: none|low|high\n"
        "- flags: array of strings\n"
        "- evidence: array of objects with fields {type, snippet, rationale}\n"
        "- summary: 1-3 sentences explaining the decision in plain language\n\n"
        f"URL: {url}\n"
        f"Image URLs (for reference): {image_urls}\n"
        f"Text:\n{text}"
    )


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def analyze_content(url: str, text_lines: List[str], image_urls: List[str]) -> Dict[str, Any]:
    if not SETTINGS.claude_api_key:
        raise RuntimeError("CLAUDE_API_KEY is not set")

    text = _truncate_text(text_lines)
    prompt = _build_prompt(url, text, image_urls)
    content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
    content.extend(_collect_images(image_urls))

    client = anthropic.Anthropic(api_key=SETTINGS.claude_api_key)
    message = client.messages.create(
        model=SETTINGS.anthropic_model,
        max_tokens=512,
        system="You are a content safety classifier. Respond with JSON only.",
        messages=[{"role": "user", "content": content}],
    )

    raw = "".join(
        part.text for part in message.content if getattr(part, "type", "") == "text"
    ).strip()
    parsed = _extract_json(raw)
    return {
        "site_context": parsed.get("site_context", ""),
        "risk_level": parsed.get("risk_level", "none"),
        "flags": parsed.get("flags") or [],
        "evidence": parsed.get("evidence") or [],
        "summary": parsed.get("summary", ""),
    }
