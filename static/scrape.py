import argparse
import json
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; URLValidatorBot/1.0; +https://example.com/bot)"
}


def normalize_url(raw: str) -> str:
    raw = raw.strip()
    parsed = urlparse(raw)
    if parsed.scheme:
        return raw
    return f"https://{raw}"


def fetch_html(url: str, timeout: int = 15, headers: Dict[str, str] | None = None) -> str:
    response = requests.get(url, timeout=timeout, headers=headers or DEFAULT_HEADERS)
    response.raise_for_status()
    return response.text


def extract_text(soup: BeautifulSoup) -> List[str]:
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    texts: List[str] = []
    for element in soup.find_all(["p", "h1", "h2", "h3", "li"]):
        text = element.get_text(separator=" ", strip=True)
        if text:
            texts.append(text)
    return texts


def extract_images(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    images: List[Dict[str, str]] = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        absolute_src = urljoin(base_url, src)
        alt = img.get("alt") or ""
        images.append({"src": absolute_src, "alt": alt})
    return images


def parse_page(html: str, base_url: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    text_blocks = extract_text(soup)
    images = extract_images(soup, base_url)

    return {
        "url": base_url,
        "title": title,
        "text": text_blocks,
        "images": images,
    }


def scrape_static(url: str, timeout: int = 15) -> Dict[str, Any]:
    normalized = normalize_url(url)
    html = fetch_html(normalized, timeout=timeout)
    return parse_page(html, normalized)


def derive_output_filename(url: str) -> Path:
    parsed = urlparse(url)
    host = parsed.netloc or "output"
    safe_host = host.replace(":", "-")
    return Path(f"{safe_host}.json")


def save_json(data: Dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple web scraper for text and images.")
    parser.add_argument("url", help="URL of the page to scrape.")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Path to output JSON file. Defaults to '<host>.json'.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    url: str = args.url

    try:
        data = scrape_static(url)
    except requests.RequestException as exc:
        raise SystemExit(f"Failed to fetch '{url}': {exc}")

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = derive_output_filename(url)

    save_json(data, output_path)
    print(f"Wrote scraped data to {output_path.resolve()}")


if __name__ == "__main__":
    main()

