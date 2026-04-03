"""FastAPI webhook server with authentication and run locking."""

from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.pipeline import Pipeline
from src.settings import settings

logger = logging.getLogger(__name__)

_run_lock = threading.Lock()
_current_run_id: str | None = None

security = HTTPBearer()


def verify_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not settings.api_auth_token:
        raise HTTPException(status_code=500, detail="API_AUTH_TOKEN not configured")
    if credentials.credentials != settings.api_auth_token:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    return credentials


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Money in Motion server starting")
    yield


app = FastAPI(title="Money in Motion Pipeline", lifespan=lifespan)


@app.post("/run")
async def trigger_run(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(verify_auth),
    lookback_hours: int | None = None,
    detectors: str | None = None,
):
    global _current_run_id

    if not _run_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail=f"Run in progress: {_current_run_id}")

    try:
        detector_list = detectors.split(",") if detectors else None
        pipeline = Pipeline(dry_run=False)

        result = pipeline.run(lookback_hours=lookback_hours, detectors=detector_list)
        _current_run_id = result.run_id

        return {
            "run_id": result.run_id,
            "status": result.status,
            "events_detected": result.events_detected,
            "events_new": result.events_new,
            "t1_count": result.t1_count,
            "t2_count": result.t2_count,
            "t3_count": result.t3_count,
            "alerts_sent": result.alerts_sent,
            "errors": result.errors,
            "api_cost_estimate": result.api_cost_estimate,
        }
    finally:
        _current_run_id = None
        _run_lock.release()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "run_in_progress": _current_run_id is not None}


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)
