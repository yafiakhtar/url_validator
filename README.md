Project: Design an API which receives a website url and performs periodic analysis on and will notify a customer if there's an issue with the website content like photos of guns or risky keywords like guns, drugs, etc.

Idea: User gives URL. That website is a web scraped for text and images. This occurs periodically/recurring. The text and images that were scraped are given to an LLM with a prompt that will let us know if it has any risky text or images. If it does, we get notified.

**Implemenation**

1. **Scrapers for static and dynamic sites** (Beautiful Soup + Playwright)
2. **LLM analysis** of scraped text and images to flag risky content (e.g. guns, drugs).
3. **Webhook notifications** when risk is detected (with retries and backoff).
4. **Scheduled runs** — each URL runs on its own interval (APScheduler).
5. **REST API** — create/update/delete jobs, list runs, health check.
6. **UI** — add URLs, set interval and mode, view jobs and run history.
7. **Content hashing** — skip LLM when the page hasn’t changed since last run.
8. **SQLite storage** — jobs, runs, and last state per job (for hashing and risk level).

**Tech stack**

- **Backend:** Python 3, FastAPI, Uvicorn
- **Scheduling:** APScheduler
- **Scraping:** Beautiful Soup 4, Playwright
- **LLM / analysis:** Anthropic (Claude)
- **HTTP:** httpx, requests
- **Data / config:** Pydantic, python-dotenv
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Hosting:** Railway

