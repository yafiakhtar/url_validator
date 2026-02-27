from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db import fetch_all
from app.runner import run_job


class SchedulerManager:
    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler()

    def start(self) -> None:
        self._scheduler.start()
        self._schedule_existing_jobs()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)

    def _schedule_existing_jobs(self) -> None:
        rows = fetch_all("SELECT id, interval_seconds, status FROM jobs")
        for row in rows:
            if row["status"] != "active":
                continue
            self.schedule_job(row["id"], row["interval_seconds"])

    def schedule_job(self, job_id: str, interval_seconds: int) -> None:
        self._scheduler.add_job(
            run_job,
            trigger=IntervalTrigger(seconds=interval_seconds),
            id=f"job-{job_id}",
            args=[job_id],
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    def remove_job(self, job_id: str) -> None:
        try:
            self._scheduler.remove_job(f"job-{job_id}")
        except Exception:
            return
