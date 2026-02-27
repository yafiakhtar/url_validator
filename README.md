Project: Design an API which receives a website url and performs periodic analysis on and will notify a customer if there's an issue with the website content like photos of guns or risky keywords like guns, drugs, etc.

Initial: User gives URL. That website is a web scraped for text and images. This occurs periodically/recurring. The text and images that were scraped are given to an LLM with a prompt that will let us know if it has any risky text or images. If it does, we get notified.

1. made scrapers for static and dynamic sites (beautifulsoup and playwright)

## API usage

### Setup
- Create a virtualenv
- Install dependencies:
  - `pip install -r requirements.txt`
  - `pip install -r static/requirements.txt`
  - `pip install -r dynamic/requirements.txt`
- Install Playwright browsers: `playwright install`
- Export env vars:
  - `CLAUDE_API_KEY=...`
  - Optional: `ANTHROPIC_MODEL=claude-3-5-sonnet-20241022`
- Or put them in a `.env` file at the project root.

### Run
- `uvicorn app.main:app --reload`

### Endpoints
- `POST /jobs` with `{ url, interval_seconds, mode, webhook_url }`
- `GET /jobs`
- `PATCH /jobs/{id}` to pause or change interval/mode/webhook
- `POST /jobs/{id}/run` for manual trigger
- `GET /jobs/{id}/runs`

