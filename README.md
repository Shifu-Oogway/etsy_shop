# AI Etsy System v3

A fully automated Etsy digital-product business platform. Local and cloud AI discover what buyers are searching for, design a product around it, generate the actual sellable file plus listing mockup images, optimize the listing for Etsy search, quality-check everything, and publish — end to end, on a schedule, with no manual steps required.

**Stack:** FastAPI · PostgreSQL + pgvector · Celery + Redis · Next.js 14 · Docker Compose · NVIDIA NIM + Ollama
**Status:** 184/184 tests passing · 9 agents · 11 database tables · 27 API routes · 7 Docker services

---

## 1. What it does

Every morning (or on demand from the dashboard), the system runs this pipeline:

```
TREND ──► STRATEGY ──► BUILDER ──► SEO ──► QA ──► PUBLISHER
 real      product      file +     title,   gate:   Etsy
 market    concept +    mockup     desc,    score   listing
 data      dedup gate   images     13 tags  ≥ 0.75  (or dry-run)
```

1. **Trend** pulls real buyer search queries from Etsy autocomplete and Google suggestions, then has the AI score the most promising opportunities. If both sources are unreachable it falls back to AI-only ideation, and every trend is labelled with its source.
2. **Strategy** turns the best trend into a concrete product concept (title, description, type, price). A deduplication gate blocks anything ≥82% similar to an existing product (lexical match always, semantic embedding match when Ollama is reachable). Manual overrides are supported for type, niche, title, price, and the dedup gate itself.
3. **Builder** merges the AI's design with a curated template library (10 niches × 3 product types — see §5), generates the real file, and renders two PNG listing mockup images per product.
4. **SEO** writes the optimized Etsy title, long-form description, and exactly 13 tags.
5. **QA** scores the product: 60% deterministic checks — including opening the actual file and validating its contents — plus 40% AI review. Products below 0.75 never reach the publisher.
6. **Publisher** creates the Etsy listing. With `ETSY_DRY_RUN=true` (the default) nothing touches a live shop; the full pipeline still runs and records fake `dryrun-*` listing IDs.

Three more agents run alongside the pipeline: **Analytics** (totals, revenue, and per-listing view/favorite sync from Etsy), **Experiment** (A/B listing variants), and the **Orchestrator** that chains everything and stops at the first failure with the reason stored.

## 2. Architecture

Seven Docker Compose services:

| Service    | Role                                                        | Port |
|------------|-------------------------------------------------------------|------|
| `db`       | PostgreSQL 16 with pgvector extension                       | 5432 |
| `redis`    | Celery broker + result backend                              | 6379 |
| `migrate`  | Runs Alembic migrations once at startup, logs fully visible | —    |
| `api`      | FastAPI backend                                             | 8000 |
| `worker`   | Celery worker executing agent jobs                          | —    |
| `beat`     | Celery beat — built-in schedule + per-minute DB dispatcher  | —    |
| `frontend` | Next.js dashboard                                           | 3000 |

Ollama runs natively on Windows and is reached from containers via `host.docker.internal:11434`.

### AI backends — NIM first, Ollama fallback

All generation goes through a unified client (`backend/app/services/ai_client.py`):

1. **NVIDIA NIM** (`https://integrate.api.nvidia.com/v1`) is used whenever an API key is set — either `NIM_API_KEY` or `NVIDIA_API_KEY` works. Auth errors (401/403) fail immediately without retry.
2. **Ollama** (local) takes over automatically on any NIM failure; the fallback is logged at WARNING. Embeddings always use Ollama.

Health for both backends is probed concurrently (3s timeout each) and reported with a specific status — `healthy`, `no_key`, `invalid_key`, `timeout`, or `unreachable` — shown on the dashboard's AI backend card.

### Data model (11 tables)

`products`, `listings` (with live `stats` JSON: views/favorites), `trends`, `seo_metadata`, `qa_reports`, `sales`, `experiments`, `task_runs` (every Celery job with full tracebacks), `embeddings` (pgvector, JSON fallback on SQLite), `schedules` (dashboard-managed cron), `event_logs` (the live activity feed).

## 3. The dashboard

Dark-themed Next.js app at `http://localhost:3000` with seven pages:

- **Overview** — stat cards (revenue, listings, pipeline, AI backend, top product), revenue sparkline, quick actions, live activity feed, latest products.
- **Products** — full table; clicking a row opens the product drawer: mockup images, type-aware file preview (embedded PDF viewer / spreadsheet table / rendered markdown), inline **Edit** (title, description, price — content edits reset QA), **Run QA**, **Publish**, and **Download**.
- **Listings** — view/favorite totals, inline title/price editing that pushes to Etsy (or dry-runs), per-listing stats refresh.
- **Trends** — discover button hits real market sources; every trend row has a **▶ Build product** button that runs the pipeline from that exact trend.
- **Agents** — run any of the nine agents individually with full error display.
- **Schedules** — create, pause, and delete cron schedules with presets; dispatched every minute by Celery from the database, so timing changes need no rebuild.
- **Test Runner** — runs the full pytest suite from the browser, streaming per-test results grouped by file, with inline tracebacks and a raw output panel. Disabled automatically in production.

A **+ New product** button in the topbar opens a guided modal: pick the product type (PDF planner / Excel template / Notion template), choose Auto (AI picks from trends) or Manual (your title), select a niche from 10 presets or type your own, optionally set a price, then watch the pipeline run step by step.

Live updates arrive over Server-Sent Events — agent events appear the moment they happen, and "Last sync" shows **live** while connected. Polling (15s) remains as fallback.

### Authentication

Set `DASHBOARD_API_KEY` in `.env` and every API request requires the key (`X-API-Key` header; query param for SSE/iframes which can't set headers). The frontend presents a lock screen and stores the key locally after unlock. Empty key = auth disabled, the default for local development.

## 4. File generation

Each product type produces a genuinely sellable file (`backend/app/services/file_generator.py`):

- **PDF planner** — multi-page PDF via reportlab: cover page, styled headers, accent rules, and ruled writing lines per section. Falls back to a print-ready HTML file if reportlab is missing.
- **Excel template** — .xlsx via openpyxl: merged title row, colored header row, 10 alternating-shade template rows with header-aware sample values, auto column widths, frozen panes. Falls back to a CSV zip bundle.
- **Notion template** — rich Markdown (callouts, tables, checkbox lists chosen by content type) plus a companion JSON spec for the Notion API.

Every build also renders **two PNG mockup images** (Pillow): a hero cover card on a per-type gradient and a type-specific detail view (spreadsheet grid for Excel, section cards for planners/Notion). Heavy libraries are optional imports — a missing dependency degrades output, never blocks the pipeline or the Docker build.

## 5. Template library

`backend/app/services/template_library.py` contains 30 hand-built product structures: 10 niches (Finance, Health & Fitness, Productivity, Business & Freelance, Wedding, Student, Travel, Meal Planning, Real Estate, Content Creator) × 3 file types. Niche matching is fuzzy — "budget planner", "Finance & Budgeting", and "money" all resolve to the finance set.

The builder feeds the matched template to the AI as a starting point and merges the result back over it, so every product meets a detail floor (≥4 pages / ≥3 sheets / ≥4 blocks) even when the model returns something thin — and if the AI is completely unavailable, the library alone still ships a complete product.

## 6. Configuration (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://etsy:etsy@db:5432/etsy` | Must use `+asyncpg`; plain `postgresql://` is auto-corrected with a logged warning |
| `REDIS_URL` | `redis://redis:6379/0` | Celery broker/backend |
| `NIM_API_KEY` / `NVIDIA_API_KEY` | empty | Either name enables NVIDIA NIM as primary AI |
| `NIM_MODEL` | `meta/llama-3.1-8b-instruct` | NIM model |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Local Ollama (fallback + embeddings) |
| `OLLAMA_MODEL` | `llama3.1:8b` | Ollama generation model |
| `ETSY_API_KEY`, `ETSY_SHOP_ID` | empty | Etsy Open API v3 credentials |
| `ETSY_DRY_RUN` | `true` | Keep true until output quality is verified |
| `DASHBOARD_API_KEY` | empty | Set to lock the dashboard/API |
| `QA_MIN_SCORE` | `0.75` | Publish gate threshold |
| `MAX_PRODUCTS_PER_DAY` | `5` | Pipeline output cap |

## 7. Operations (PowerShell, Windows)

All scripts are PowerShell 5.1-compatible (no `?.`, LF endings, ASCII-only, `$LASTEXITCODE` checked, no suppressed output):

| Script | Purpose |
|---|---|
| `scripts\install.ps1` | First-time build of all images |
| `scripts\start-system.ps1` / `stop-system.ps1` | Bring the stack up / down (volumes preserved) |
| `scripts\update.ps1 -Zip path.zip` | **Apply any update**: lists zip contents, snapshots overwritten files to `backups\<timestamp>`, extracts, rebuilds, rolling-restarts, streams migration logs, health-checks — and auto-restores on build failure. Rollback: `update.ps1 -Rollback "backups\<timestamp>"` |
| `scripts\reset.ps1` | Full wipe (volumes, images, `.env` → fresh from template with `.env.bak` backup) and rebuild; requires typing `YES` |
| `scripts\register-task-scheduler.ps1` | Windows Task Scheduler auto-start |

Full installation walkthrough in §8, daily usage in §9.

Scheduling runs two ways simultaneously: the built-in beat schedule (05:30 trend scan, 06:00 full pipeline, hourly analytics) and dashboard-managed cron schedules dispatched from the database every minute.

## 8. Setup — from zero to running

### Prerequisites

1. **Docker Desktop for Windows** — [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop). During install select the **WSL 2 backend**. After installing, start it and wait until the whale icon in the system tray reports "Docker Desktop is running". Verify with `docker info` in PowerShell.
2. **Ollama** (local AI fallback + embeddings) — [ollama.com](https://ollama.com). After install, pull the two models the system uses:
   ```powershell
   ollama pull llama3.1:8b
   ollama pull nomic-embed-text
   ```
   Confirm it's serving with `ollama list`. It must stay running on Windows — containers reach it via `host.docker.internal:11434`.
3. **NVIDIA NIM key** (recommended primary AI) — create a free account at [build.nvidia.com](https://build.nvidia.com), generate an API key (starts with `nvapi-`). The free tier includes credits.
4. **Etsy API credentials** (only needed for live publishing) — register an app at [etsy.com/developers](https://www.etsy.com/developers) to get an API key, and note your shop ID. Skip this for now if you only want dry-run mode.

### Installation

```powershell
# 1. Extract the project
tar -xzf ai-etsy-system-v3.tar.gz -C D:\

# 2. Allow local scripts to run (one time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3. Create your environment file
cd D:\ai-etsy-system
Copy-Item .env.example .env
notepad .env
```

In `.env`, set at minimum:
```properties
NVIDIA_API_KEY=nvapi-your-key-here     # or NIM_API_KEY — both work
ETSY_API_KEY=                          # leave empty for now
ETSY_SHOP_ID=                          # leave empty for now
ETSY_DRY_RUN=true                      # keep true until §9 "Going live"
DASHBOARD_API_KEY=                     # optional: set to lock the dashboard
```
Everything else works as-is for the Docker setup.

```powershell
# 4. Build all images (5-10 minutes the first time)
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1

# 5. Start the stack
powershell -ExecutionPolicy Bypass -File .\scripts\start-system.ps1
```

### Verify it works

Open `http://localhost:3000` — the Overview page should load. Check the **AI backend** card: it should read `NIM · meta/llama-3.1-8b-instruct`. If it reads `Ollama · llama3.1:8b (no NIM key)` your key isn't being picked up; `(invalid NIM key)` means the key is wrong. The API health detail is at `http://localhost:8000/api/v1/system/health`, interactive API docs at `http://localhost:8000/docs`. Finally, open the **⬡ Test Runner** page and hit **Run all tests** — expect 184/184 green.

Optional: `.\scripts\register-task-scheduler.ps1` makes the stack start automatically with Windows.

## 9. How to use it

### Your first product (manual, ~2 minutes)

1. Click **+ New product** in the topbar.
2. Pick a type — PDF Planner, Excel Template, or Notion Template.
3. Choose **Auto** (AI selects niche and title from market trends) or **Manual** (you type the title). Optionally pick a niche and price.
4. Click **Generate product** and watch the pipeline run: Trend → Strategy → Build → SEO → QA → Publish, with per-step ✓/✕ status.
5. Open **Products**, click the new row. The drawer shows the mockup images, a rendered preview of the actual file, and a **Download** button.

### Building from real market data

Open **Trends** → **🔍 Discover trends**. The system pulls live Etsy and Google search suggestions and scores them ("real data" badge) — rows marked "AI only" mean the sources were unreachable. Click **▶ Build product** on any trend to run the pipeline against that exact buyer search.

### Reviewing and editing before publishing

Products that fail QA (or that you want to polish) are edited in the drawer: **✎ Edit** to change title, description, or price → **Save** → **Run QA** (content edits always require re-passing the gate) → **🚀 Publish** once status is `qa_passed`. In dry-run mode publishing creates a `dryrun-*` listing you can inspect on the **Listings** page without touching Etsy.

### Managing listings

The **Listings** page shows views and favorites per listing (simulated-but-plausible numbers in dry-run, real Etsy stats live). **Edit** changes title/price and pushes the update to Etsy; **↻ Stats** refreshes one listing's numbers. The hourly analytics agent refreshes all of them automatically.

### Automation

Out of the box, beat runs the trend scan at 05:30, the full pipeline at 06:00, and analytics hourly. Add your own timing on the **◷ Schedules** page — pick an agent, a cron preset (or write your own five-field cron), and the dispatcher fires it within a minute of matching. Pause or delete schedules anytime; no rebuild needed.

### Going live on Etsy

When dry-run products consistently look sellable: fill `ETSY_API_KEY` and `ETSY_SHOP_ID` in `.env`, flip `ETSY_DRY_RUN=false`, then `.\scripts\stop-system.ps1` and `.\scripts\start-system.ps1`. From that point publishes create real draft listings in your shop. Recommendation: keep `MAX_PRODUCTS_PER_DAY` low (3–5) initially and review the first week's output daily.

### Applying updates

Every future change ships as a zip of only the changed files:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\update.ps1 -Zip "C:\Users\chris\Downloads\full-feature-update.zip"
```
It snapshots what it overwrites, rebuilds, restarts, streams migration logs, and health-checks — printing a one-line rollback command if you ever need to undo. `.\scripts\reset.ps1` is the nuclear option: full wipe and rebuild (it backs up `.env` to `.env.bak` first).

### When something breaks

The dashboard never hides errors — failed agent runs show full tracebacks in the Agents page and the activity feed. For container-level issues: `docker compose logs api` (or `worker`, `beat`, `migrate`, `frontend`). The **Test Runner** page is the fastest way to confirm the codebase itself is healthy after an update.

## 10. Testing

184 tests run against in-memory SQLite and a deterministic fake AI client — no services needed: `python -m pytest tests/` from `backend/`, or use the dashboard's Test Runner page. Coverage spans module imports, models, all agents (including a full orchestrator pipeline run), API routes, file generators, the template library (every niche × type), deduplication, mockup rendering, cron matching, QA file validation, dry-run Etsy stats, and the auth middleware.

## 11. Engineering notes

Hard-won constraints baked into the codebase: SQLAlchemy `BigInteger` imports from the top-level package; standard `cast(col, Float)` rather than `func.cast()`; one-to-many relationships never use `uselist=False`; a single initial migration with no duplicate columns and no `GENERATED ALWAYS AS STORED`; async Alembic requires `postgresql+asyncpg://` and never suppresses startup output; Docker apt packages use exact names (`libgdk-pixbuf-2.0-0`); PowerShell scripts avoid PS7-only syntax and non-ASCII characters; update zips always preserve full directory paths; and errors everywhere are stored and surfaced in full — never swallowed.

## 12. Version history

- **v1** — initial system: 9 agents, 38 modules, 19 tests.
- **v2** — full rebuild: 83 tests, QA gate, dry-run publishing, dashboard, update/reset tooling.
- **v3 (current)** — NIM+Ollama dual AI, real market-data trends, mockup images, template library, deduplication, QA file validation, listing stats + editing, product editing/publish flow, schedule editor, SSE live feed, dashboard auth, in-browser test runner. 184 tests.