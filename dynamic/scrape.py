import argparse
import asyncio
import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright


def _normalize_url(raw: str) -> str:
    raw = raw.strip()
    parsed = urlparse(raw)
    if parsed.scheme:
        return raw
    return f"https://{raw}"


async def scrape_page(url: str, *, timeout_ms: int = 45000) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            await page.wait_for_timeout(1500)

            text = await page.locator("body").inner_text()
            text_lines = [line.strip() for line in text.splitlines() if line.strip()]

            images = await page.evaluate(
                """() => {
                  const urls = [];
                  const seen = new Set();
                  for (const img of document.images) {
                    const raw = img.currentSrc || img.src || "";
                    if (!raw) continue;
                    let abs;
                    try { abs = new URL(raw, document.baseURI).href; } catch { continue; }
                    if (!/^https?:/i.test(abs)) continue;
                    if (seen.has(abs)) continue;
                    seen.add(abs);
                    urls.push(abs);
                  }
                  return urls;
                }"""
            )

            return {"url": url, "text": text_lines, "images": images}
        finally:
            await browser.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Super simple Playwright scraper: extract page text + image URLs to JSON."
    )
    parser.add_argument("url", help="URL of the page to scrape")
    parser.add_argument(
        "--out",
        type=str,
        default="page_data.json",
        help="Output JSON path (default: page_data.json)",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=45000,
        help="Navigation timeout in milliseconds (default: 45000)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    url = _normalize_url(args.url)
    out_path = Path(args.out)

    try:
        data = asyncio.run(scrape_page(url, timeout_ms=args.timeout_ms))
    except Exception as exc:
        raise SystemExit(f"Failed to scrape '{url}': {exc}")

    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path.resolve()}")


if __name__ == "__main__":
    main()

