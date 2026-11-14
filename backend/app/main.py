"""FastAPI application entry point."""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_db

app = FastAPI(
    title="pothole-watch-blr API",
    version="0.0.1",
    description="Report, deduplicate and track potholes in Bengaluru.",
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness check used by Docker and CI. Does not touch the database."""
    return {"status": "ok"}


@app.get("/ready", tags=["meta"])
def ready(db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    """Readiness check: can the API actually reach the database?"""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="database unavailable"
        ) from exc
    return {"status": "ok"}
