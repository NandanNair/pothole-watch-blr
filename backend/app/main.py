"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="pothole-watch-blr API",
    version="0.0.1",
    description="Report, deduplicate and track potholes in Bengaluru.",
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness check used by Docker and CI. Does not touch the database."""
    return {"status": "ok"}
