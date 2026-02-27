from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, HttpUrl, Field


JobMode = Literal["static", "dynamic", "auto"]
JobStatus = Literal["active", "paused"]
RiskLevel = Literal["none", "low", "high"]
RunStatus = Literal["running", "success", "failed"]


class JobCreate(BaseModel):
    url: HttpUrl
    interval_seconds: int = Field(ge=30, le=60 * 60 * 24)
    mode: JobMode = "auto"
    webhook_url: HttpUrl


class JobUpdate(BaseModel):
    interval_seconds: Optional[int] = Field(default=None, ge=30, le=60 * 60 * 24)
    mode: Optional[JobMode] = None
    webhook_url: Optional[HttpUrl] = None
    status: Optional[JobStatus] = None


class JobOut(BaseModel):
    id: str
    url: str
    interval_seconds: int
    mode: JobMode
    webhook_url: str
    status: JobStatus
    created_at: str
    updated_at: str


class RunOut(BaseModel):
    id: str
    job_id: str
    started_at: str
    finished_at: Optional[str]
    status: RunStatus
    risk_level: Optional[RiskLevel]
    flags: Optional[list[str]]
    evidence: Optional[Any]
    raw_hash: Optional[str]
    error: Optional[str]
