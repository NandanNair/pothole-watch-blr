# PLAN — pothole-watch-blr

Status: **approved 14 Nov 2026.** Phase 0 in progress.

## 1. What we are building

A web app (installable PWA) where a person photographs a pothole, the server detects it
with a fine-tuned YOLO model, merges duplicate reports of the same pothole, shows them on
a public map, and produces a ready-to-send complaint for the Greater Bengaluru Authority (GBA).

Working assumptions from your answers: beginner in Python, JS and ML; 5–8 hours a week;
no deadline; training on free Colab/Kaggle GPUs; public repo `pothole-watch-blr`, MIT.

## 2. Research: how complaints reach the GBA today

Researched 14 Nov 2026 from news reports and public listings. I could not open the GBA's
own site, so anything marked *unverified* must be re-checked before Phase 4.

| Channel | What I found | Confidence |
|---|---|---|
| Governance | BBMP was replaced in Sept 2025 by the GBA with five city corporations; complaints route to the corporation covering the location. | High |
| Helpline | 1533 (toll-free ICCC) and 080-22221188, posted by the official GBA X account; potholes are listed as reportable. | High |
| App | "Namma Bengaluru" / Sahaaya 2.0 is the tracked grievance app (about 300 grievances a day). App Store reviews complain that no confirmation or history is shown after filing. | Medium |
| Older apps | Fix My Street, PACE, Pothole Fix, Raste Gundi Gamana (2017–2024). Current status unknown; assume dead. | Low |
| WhatsApp | Two different numbers appear in third-party guides, both BBMP-era. | *Unverified — will not be used* |
| Email | comm@bbmp.gov.in appears in one guide; domain predates the GBA. | *Unverified — will not be used* |
| Public API | **None found.** No documented API for filing or tracking complaints. | High |

**Decision.** No official API, so submission is a pluggable `SubmissionChannel` interface with two implementations:

1. `MockChannel` — for tests and demos; simulates submitted → acknowledged → fixed.
2. `DraftChannel` — generates a complaint packet (blurred photo, coordinates, map link,
   address, ward/corporation, severity, report count) that the user reviews, then files
   themselves in the Namma Bengaluru app or by calling 1533. The user pastes the ticket
   number back, and status updates are entered manually.

We will **not** scrape or automate the official app, and will not auto-send anything on a
user's behalf. Status tracking is therefore self-reported, and the docs will say so.

**Prior art.** A similar open-source project exists: `deepanshu-iitm/pothole-reporter`
(on-device Android, drafts emails). Ours differs by being a web PWA with PostGIS
deduplication, a public dashboard, and a published model evaluation. The README will
acknowledge it rather than claim novelty.

## 3. Architecture

```
Phone/browser (React PWA)
   │  photo + GPS + note (HTTPS, JWT)
   ▼
FastAPI ──► image pipeline: validate → strip EXIF → detect (ONNX) → blur faces/plates → save
   │
   ├──► PostgreSQL + PostGIS   (users, reports, tickets, submissions)
   ├──► file storage           (blurred images only; local volume, swappable for S3)
   └──► SubmissionChannel      (Mock | Draft)
```

The original, unblurred photo is never written to disk. It is held in memory, processed,
and discarded.

## 4. Tech choices

| Area | Choice | Why |
|---|---|---|
| Frontend | React + Vite + TypeScript, `vite-plugin-pwa`, Leaflet + OpenStreetMap tiles | **Change from the suggestion:** Vite instead of Next.js. We have a separate API and no need for server rendering, so Next.js adds concepts with no benefit. Leaflet is the simplest map library. |
| Backend | FastAPI, SQLAlchemy 2, GeoAlchemy2, Alembic, Pydantic | As suggested. Auto-generated API docs help you learn and demo it. |
| Auth | Email + password, Argon2 hashes, JWT access tokens | No third-party OAuth setup; you can explain every line. |
| Rate limiting | `slowapi` (per-IP and per-user) | Small, standard for FastAPI. |
| Database | PostgreSQL 16 + PostGIS | Spatial index and `ST_DWithin` do the deduplication in SQL. |
| ML training | Ultralytics YOLO11n in a Colab notebook, results logged to CSV + committed plots | Easiest toolchain for a beginner. See licence note below. |
| ML serving | ONNX Runtime on CPU inside the API | No GPU needed to host; no PyTorch in the production image. |
| Privacy blur | OpenCV YuNet for faces; an open ONNX number-plate detector (to be chosen and measured in Phase 1) | Blur is a hard requirement from the first stored image. |
| Geocoding | Nominatim (OpenStreetMap), cached, max 1 request/second | Free; usage policy respected. |
| Tooling | Docker Compose, pytest, ruff (lint + format), ESLint, Vitest, pre-commit, GitHub Actions | **Change:** ruff's formatter replaces black — one tool instead of two. |

### Things you need to decide or know about

- **Model licence.** Ultralytics YOLO is AGPL-3.0, and Ultralytics treats trained weights
  as AGPL too. Proposal: app code stays MIT, the training notebook and released weights are
  labelled AGPL-3.0, and the API only loads the ONNX file through ONNX Runtime. If you want
  everything permissive, the alternative is YOLOX (Apache-2.0), which is harder to use.
- **Dataset licence.** RDD2022 is CC BY-SA 4.0 (to be confirmed against the original
  Figshare release in Phase 2). We never commit the data, and we credit it.
- **Dataset fit.** RDD2022's India images are from Delhi, Gurugram and Haryana, shot from
  car-mounted phones. Your users will take handheld close-ups in Bengaluru. Expect a
  real accuracy drop; your own test photos in Phase 2 exist to measure it honestly.
- **Blur is imperfect.** No detector catches every face or plate. We will measure the miss
  rate on a small labelled set and state it in the README.

## 5. Folder structure

```
pothole-watch-blr/
├── backend/
│   ├── app/            api/  core/  models/  schemas/  services/  channels/
│   ├── alembic/
│   ├── tests/
│   └── pyproject.toml
├── frontend/           src/ (pages, components, api client)  public/
├── ml/                 notebooks/  scripts/ (download, prepare, export)  README.md
├── docs/               EVALUATION.md  DECISIONS.md  images/
├── .github/workflows/  ci.yml
├── docker-compose.yml
├── .env.example  .gitignore  .pre-commit-config.yaml  LICENSE  README.md  PLAN.md
```

## 6. Phases

Estimates assume 5–8 hours a week. Each phase is one branch, one milestone, one PR, merged
only after CI is green and you have reviewed it.

| Phase | Scope | Done when | Estimate |
|---|---|---|---|
| 0. Setup | Repo, licence, CI skeleton, issues and milestones, Docker Compose booting an empty API + DB | CI badge is green on `main` | 1 week |
| 1. Manual MVP | Register/login, submit report (photo, editable GPS, note), EXIF strip + blur, map and list views, rate limits, validation, API tests | You can file a report from your phone on local Wi-Fi and see it on the map | 3 weeks |
| 2. Detection | Download + prepare RDD2022, train YOLO11n, evaluate on held-out test set, export ONNX, auto-classify uploads, flag non-potholes for review | `docs/EVALUATION.md` has real precision, recall and mAP; weights on GitHub Releases | 3 weeks |
| 3. Dedup + severity | Cluster reports within a configurable radius (default 10 m) into tickets with a reporter count; severity from detected box area and report count; edge-case tests | Boundary and same-user duplicate tests pass | 2 weeks |
| 4. Complaints | Complaint generation, reverse geocoding, ward/corporation lookup if open boundary data is usable, Mock + Draft channels, status tracking | A complaint packet can be generated and its status tracked end to end | 2 weeks |
| 5. Dashboard | Public map and stats: open tickets, average days open, worst roads/wards, resolution rate | Dashboard works on seeded demo data, clearly labelled as demo | 1 week |
| 6. Passive detection | Only if you ask | — | — |

Deployment: decided at the end of Phase 1 (likely a free-tier host plus a managed
Postgres with PostGIS). Phases 1–3 deployed and documented is the target; 4–5 are a bonus.

## 7. Testing and CI

- Backend tests run against a real PostGIS container, not SQLite, because the spatial
  queries are the part most worth testing.
- CI on every push and PR: ruff, pytest, ESLint, Vitest, frontend build.
- Dashboard and README numbers come only from things we actually ran.

## 8. Local prerequisites

- Git, Python 3.12, Node.js 26 LTS, GitHub CLI (`gh auth login`)
- Docker Desktop, which needs WSL2 on Windows (`wsl --install`, then reboot)
- Keep the project outside OneDrive or other synced folders; syncing `node_modules` and
  Docker files causes slowdowns and file-lock errors.
