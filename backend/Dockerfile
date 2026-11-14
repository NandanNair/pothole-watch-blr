FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

COPY pyproject.toml ./
COPY app ./app
# A generous timeout so slow connections do not fail the build.
RUN pip install --no-cache-dir --default-timeout=120 .

COPY alembic.ini ./
COPY alembic ./alembic

# Run as a non-root user so a bug in the app cannot modify the image.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
# Apply any pending migrations, then start the server.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
