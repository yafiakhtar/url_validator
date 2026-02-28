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

## Local test guide

### 1) Install dependencies
- Create and activate a virtualenv
- Install everything:
  - `pip install -r requirements.txt`
- Install Playwright browsers:
  - `playwright install`

### 2) Configure environment
Create a `.env` file in the project root with:
```
CLAUDE_API_KEY=your_key_here
ANTHROPIC_MODEL=your_model_id
```
Optional:
```
DB_PATH=./data/app.db
```

### 3) Run the API (serves the UI too)
```
python -m uvicorn app.main:app --reload
```

### 4) Use the web UI
Open:
```
http://127.0.0.1:8000/
```
Steps:
1. Enter a URL
2. Choose the check frequency
3. Click **Add job**
4. Click **Run now** to trigger a one-time analysis

The UI will show:
- **Loading** while processing
- **Safe** if no risk
- **Risk;** with flags if risky content is detected

Alerts appear at the top if any job is flagged.

### 5) Verify it runs periodically
If no content changes, the job still runs on schedule, but Claude is skipped.
You can confirm periodic runs via:
```
GET /jobs/{id}/runs
```
You should see new run entries with updated timestamps even when no alerts change.

### 6) Optional: test with PowerShell scripts
Create a job:
```
.\create_job.ps1
```
Run once:
```
.\run_job.ps1 -JobId <JOB_ID>
```
List runs:
```
.\list_runs.ps1 -JobId <JOB_ID>
```
Pause a job:
```
.\pause_job.ps1 -JobId <JOB_ID>
```
