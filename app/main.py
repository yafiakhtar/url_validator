from __future__ import annotations

import uuid
from typing import List

from fastapi import BackgroundTasks, FastAPI, HTTPException

from app.db import execute, fetch_all, fetch_one, init_db, parse_json
from app.models import JobCreate, JobOut, JobUpdate, RunOut
from app.runner import run_job
from app.scheduler import SchedulerManager
from app.utils import utc_now

app = FastAPI(title="URL Risk Monitor API")
scheduler = SchedulerManager()


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    scheduler.start()


@app.on_event("shutdown")
def on_shutdown() -> None:
    scheduler.shutdown()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/jobs", response_model=JobOut)
def create_job(payload: JobCreate) -> JobOut:
    job_id = str(uuid.uuid4())
    now = utc_now()
    execute(
        """
        INSERT INTO jobs (id, url, interval_seconds, mode, webhook_url, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            str(payload.url),
            payload.interval_seconds,
            payload.mode,
            str(payload.webhook_url),
            "active",
            now,
            now,
        ),
    )
    scheduler.schedule_job(job_id, payload.interval_seconds)
    row = fetch_one("SELECT * FROM jobs WHERE id = ?", (job_id,))
    return JobOut(**row)


@app.get("/jobs", response_model=List[JobOut])
def list_jobs() -> List[JobOut]:
    rows = fetch_all("SELECT * FROM jobs ORDER BY created_at DESC")
    return [JobOut(**row) for row in rows]


@app.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str) -> JobOut:
    row = fetch_one("SELECT * FROM jobs WHERE id = ?", (job_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobOut(**row)


@app.patch("/jobs/{job_id}", response_model=JobOut)
def update_job(job_id: str, payload: JobUpdate) -> JobOut:
    row = fetch_one("SELECT * FROM jobs WHERE id = ?", (job_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    updates = []
    params = []

    if payload.interval_seconds is not None:
        updates.append("interval_seconds = ?")
        params.append(payload.interval_seconds)
    if payload.mode is not None:
        updates.append("mode = ?")
        params.append(payload.mode)
    if payload.webhook_url is not None:
        updates.append("webhook_url = ?")
        params.append(str(payload.webhook_url))
    if payload.status is not None:
        updates.append("status = ?")
        params.append(payload.status)

    if updates:
        updates.append("updated_at = ?")
        params.append(utc_now())
        params.append(job_id)
        execute(f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?", tuple(params))

    updated = fetch_one("SELECT * FROM jobs WHERE id = ?", (job_id,))
    if updated["status"] == "active":
        scheduler.schedule_job(job_id, updated["interval_seconds"])
    else:
        scheduler.remove_job(job_id)
    return JobOut(**updated)


@app.delete("/jobs/{job_id}")
def delete_job(job_id: str) -> dict:
    row = fetch_one("SELECT * FROM jobs WHERE id = ?", (job_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    execute("DELETE FROM runs WHERE job_id = ?", (job_id,))
    execute("DELETE FROM job_state WHERE job_id = ?", (job_id,))
    execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    scheduler.remove_job(job_id)
    return {"status": "deleted"}


@app.get("/jobs/{job_id}/runs", response_model=List[RunOut])
def list_runs(job_id: str) -> List[RunOut]:
    rows = fetch_all("SELECT * FROM runs WHERE job_id = ? ORDER BY started_at DESC", (job_id,))
    output = []
    for row in rows:
        row = dict(row)
        row["flags"] = parse_json(row.get("flags"))
        row["evidence"] = parse_json(row.get("evidence"))
        output.append(RunOut(**row))
    return output


@app.post("/jobs/{job_id}/run")
def run_job_now(job_id: str, background_tasks: BackgroundTasks) -> dict:
    row = fetch_one("SELECT * FROM jobs WHERE id = ?", (job_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    background_tasks.add_task(run_job, job_id)
    return {"status": "queued"}
