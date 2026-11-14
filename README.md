# pothole-watch-blr

[![CI](https://github.com/NandanNair/pothole-watch-blr/actions/workflows/ci.yml/badge.svg)](https://github.com/NandanNair/pothole-watch-blr/actions/workflows/ci.yml)

Report potholes in Bengaluru with a photo. The app detects the pothole, merges duplicate
reports of the same spot, maps them, and prepares a complaint for the Greater Bengaluru
Authority (GBA).

> **Status: Phase 0 (setup).** Nothing is usable yet. See [PLAN.md](PLAN.md) for the
> architecture, tech choices and roadmap.

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 0 | Repo, CI, Docker Compose skeleton | In progress |
| 1 | Manual reporting MVP | Not started |
| 2 | Pothole detection (YOLO on RDD2022) | Not started |
| 3 | Deduplication and severity | Not started |
| 4 | Complaint generation and submission channels | Not started |
| 5 | Public dashboard | Not started |

## Run it locally

Needs Docker Desktop (with WSL2 on Windows).

```bash
cp .env.example .env
docker compose up --build
```

The API is then at http://localhost:8000 and its interactive docs at http://localhost:8000/docs.

## Run the backend tests

The tests use a real PostGIS database, so start it first.

```bash
docker compose up -d db
cd backend
python -m venv .venv
.venv/Scripts/activate        # macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check . && pytest
```

## Licence

Application code: [MIT](LICENSE). Dataset and model weight licences will be documented
in `docs/DECISIONS.md` when Phase 2 lands.
