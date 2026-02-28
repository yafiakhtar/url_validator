from __future__ import annotations

import uuid
from typing import Any, Dict

from app.analysis import analyze_content
from app.db import execute, fetch_one, insert_json, parse_json
from app.notify import send_webhook
from app.scrapers import scrape_url
from app.utils import content_hash, utc_now


def _row_to_dict(row) -> Dict[str, Any]:
    return dict(row) if row else {}


def run_job(job_id: str) -> Dict[str, Any]:
    job_row = fetch_one("SELECT * FROM jobs WHERE id = ?", (job_id,))
    if not job_row:
        raise ValueError(f"Job {job_id} not found")

    job = _row_to_dict(job_row)
    if job["status"] != "active":
        return {"status": "skipped", "reason": "paused"}

    run_id = str(uuid.uuid4())
    started_at = utc_now()
    execute(
        """
        INSERT INTO runs (id, job_id, started_at, status)
        VALUES (?, ?, ?, ?)
        """,
        (run_id, job_id, started_at, "running"),
    )

    try:
        scraped = scrape_url(job["url"], job["mode"])
        text_lines = scraped.get("text") or []
        images_raw = scraped.get("images") or []
        images = []
        if isinstance(images_raw, list):
            if images_raw and isinstance(images_raw[0], dict):
                images = [img.get("src") for img in images_raw if img.get("src")]
            else:
                images = [img for img in images_raw if isinstance(img, str)]

        raw_hash = content_hash(text_lines, images)
        state_row = fetch_one("SELECT * FROM job_state WHERE job_id = ?", (job_id,))
        last_hash = state_row["last_hash"] if state_row else None

        if last_hash == raw_hash:
            finished_at = utc_now()
            last_risk_level = state_row["last_risk_level"] if state_row else None
            last_flags = parse_json(state_row["last_flags"]) if state_row else []
            last_evidence = parse_json(state_row["last_evidence"]) if state_row else []
            last_risk_at = state_row["last_risk_at"] if state_row else None
            risk_level = last_risk_level or "none"
            execute(
                """
                UPDATE runs
                SET finished_at = ?, status = ?, risk_level = ?, flags = ?, evidence = ?, raw_hash = ?, risk_at = ?
                WHERE id = ?
                """,
                (
                    finished_at,
                    "success",
                    risk_level,
                    insert_json(last_flags or []),
                    insert_json(last_evidence or []),
                    raw_hash,
                    last_risk_at,
                    run_id,
                ),
            )
            return {"status": "success", "run_id": run_id, "risk_level": risk_level}

        analysis = analyze_content(job["url"], text_lines, images)
        risk_level = analysis.get("risk_level", "none")
        flags = analysis.get("flags", [])
        evidence = analysis.get("evidence", [])

        finished_at = utc_now()
        risk_at = finished_at if risk_level in ("low", "high") else None
        execute(
            """
            UPDATE runs
            SET finished_at = ?, status = ?, risk_level = ?, flags = ?, evidence = ?, raw_hash = ?, risk_at = ?
            WHERE id = ?
            """,
            (
                finished_at,
                "success",
                risk_level,
                insert_json(flags),
                insert_json(evidence),
                raw_hash,
                risk_at,
                run_id,
            ),
        )

        if state_row:
            execute(
                """
                UPDATE job_state
                SET last_hash = ?, last_risk_level = ?, last_flags = ?, last_evidence = ?, last_risk_at = ?
                WHERE job_id = ?
                """,
                (
                    raw_hash,
                    risk_level if risk_level in ("low", "high") else None,
                    insert_json(flags) if risk_level in ("low", "high") else None,
                    insert_json(evidence) if risk_level in ("low", "high") else None,
                    risk_at,
                    job_id,
                ),
            )
        else:
            execute(
                """
                INSERT INTO job_state (job_id, last_hash, last_risk_level, last_flags, last_evidence, last_risk_at, last_notified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    raw_hash,
                    risk_level if risk_level in ("low", "high") else None,
                    insert_json(flags) if risk_level in ("low", "high") else None,
                    insert_json(evidence) if risk_level in ("low", "high") else None,
                    risk_at,
                    None,
                ),
            )

        if risk_level in ("low", "high") and job.get("webhook_url"):
            payload = {
                "job_id": job_id,
                "run_id": run_id,
                "url": job["url"],
                "risk_level": risk_level,
                "flags": flags,
                "evidence": evidence,
                "timestamp": finished_at,
            }
            send_webhook(job["webhook_url"], payload)
            execute(
                "UPDATE job_state SET last_notified_at = ? WHERE job_id = ?",
                (utc_now(), job_id),
            )

        return {"status": "success", "run_id": run_id, "risk_level": risk_level}
    except Exception as exc:
        finished_at = utc_now()
        execute(
            """
            UPDATE runs
            SET finished_at = ?, status = ?, error = ?
            WHERE id = ?
            """,
            (finished_at, "failed", str(exc), run_id),
        )
        return {"status": "failed", "run_id": run_id, "error": str(exc)}
