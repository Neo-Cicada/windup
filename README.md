# Windup Academy

A DSA interview-preparation platform with a sandboxed, multi-language code judge.

Windup Academy presents the [NeetCode roadmap](https://neetcode.io/roadmap) as a
progression system: 19 topic zones of 5 problems each, tiered hints, timed mock rounds,
and head-to-head races. Solutions are graded server-side by a judge that executes
submitted code inside a WebAssembly sandbox, in any of eight languages, against a single
set of hidden test cases.

The domain is themed — users are toys, XP is charge, hints are help chests — and that
vocabulary is used consistently throughout the codebase and API copy.

---

## Contents

- [Highlights](#highlights)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Repository layout](#repository-layout)

---

## Highlights

**Multi-language judging, one set of tests.** Python, JavaScript, Ruby, PHP, SQL, C++,
Rust and Go. Test cases are plain JSON compared on the host, so the grading path
contains no per-language logic; adding a language is a new module in a registry.

**Execution is sandboxed.** Submissions run as an interpreter-on-WASI under wasmtime,
with fuel limiting CPU, a store limit capping memory, and no preopened directory — no
filesystem, no sockets. C++, Rust and Go are compiled on the host into a WebAssembly
module that the same sandbox then runs.

**Expected values never enter the sandbox.** Only arguments are passed in and the host
performs the comparison, so submitted code cannot read the answers it is being graded
against.

**Two execution paths, deliberately separate.** *Run* executes the visible examples in
the browser (Pyodide for Python and SQL, a Web Worker for JavaScript) for instant
feedback that grades nothing and keeps the majority of executions off the server.
*Submit* queues the code for the judge, which is the sole authority on whether a problem
is solved.

**The server owns all state transitions.** The submission schema has no status field;
verdicts, XP, levels and streaks are computed server-side and returned on the response
that caused them. Hidden test cases never leave the server.

**Progression systems.** Tiered help chests (peeking forfeits the unaided bonus), timed
boss battles, real-time 1v1 duels over a shared invite link, achievements, streaks, and
an append-only XP ledger backing the analytics.

**Responsive.** Layout decisions are made in CSS rather than by measuring the viewport,
so the first paint is correct and there is nothing to reconcile on hydration.

---

## Architecture

Two independent applications in one repository, communicating over a versioned REST API.

```
┌─────────────────┐        ┌──────────────────┐        ┌─────────────┐
│  Next.js 16     │  HTTP  │  FastAPI         │        │ PostgreSQL  │
│  React 19       │ ─────► │  /api/v1         │ ─────► │             │
│                 │  JWT   │                  │        │             │
│  Pyodide / Web  │        │  submissions     │        └─────────────┘
│  Worker (Run)   │        │  queue           │               ▲
└─────────────────┘        └──────────────────┘               │
                                    │  claim                  │
                                    ▼                         │
                           ┌──────────────────┐               │
                           │  Judge worker    │ ──────────────┘
                           │  wasmtime / WASI │
                           └──────────────────┘
```

Submission is asynchronous. `POST /problems/{slug}/submit` validates and queues, then
returns `202`; a judge worker claims the job, executes it in the sandbox, grades it and
settles the payout; the client polls `GET /submissions/{id}` until the verdict is
terminal. **A judge worker is therefore a required process, not an optional one** — the
API accepts submissions without one, but nothing is ever graded.

| Layer | Stack |
| --- | --- |
| Frontend | Next.js 16 (App Router), React 19 with React Compiler, TypeScript 5 |
| Backend | FastAPI (async), Pydantic v2, SQLAlchemy 2.0 (`asyncpg`), Alembic |
| Database | PostgreSQL |
| Judge | wasmtime, WASI interpreter builds, host-side compilation for C++/Rust/Go |
| Auth | JWT access/refresh tokens, bcrypt password hashing |
| Tooling | `uv` (Python), npm (Node), ruff, pytest, ESLint |

`backend/README.md` documents the full endpoint reference, data model and judge design.

---

## Requirements

| | Version | Notes |
| --- | --- | --- |
| Python | ≥ 3.12 | Managed with [`uv`](https://docs.astral.sh/uv/) |
| Node.js | ≥ 20.9 | Required by Next.js 16 |
| PostgreSQL | — | `backend/docker-compose.yml` provides Postgres 17 |
| wasmtime | ≥ 47 | Installed as a Python dependency |

Language runtimes are fetched as prebuilt WASI artifacts and are not committed
(approximately 20MB each). C++, Rust and Go additionally require toolchains on the
worker host and may be omitted from `JUDGE_LANGUAGES` if not needed.

---

## Quickstart

Three processes are required: the API, at least one judge worker, and the frontend.

### 1. Backend

```bash
cd backend
uv sync                                # create .venv and install dependencies
cp .env.example .env                   # set DATABASE_URL and SECRET_KEY

./scripts/fetch_language_wasm.sh       # WASI builds for every offered language
./scripts/fetch_toolchains.sh          # optional: C++/Rust/Go compilers

docker compose up -d db                # or: createdb windup
uv run alembic upgrade head
uv run python -m app.db.seed --demo    # catalogue and a demo account

uv run uvicorn app.main:app --reload --port 8000
```

- API documentation: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>
- Demo account: `bramble@playroom.com` / `windup123`

### 2. Judge worker

In a separate terminal:

```bash
cd backend
uv run python -m app.judge.worker
```

The worker compiles a module for every language in `JUDGE_LANGUAGES` at startup, so a
missing artifact is a refusal to boot naming the fetch command, rather than a failed
submission discovered later.

Workers are horizontally scalable; payout is idempotent and serialised per user, so
running several is safe. If no worker is running, submissions are reported as stalled
with a diagnostic message rather than left to time out.

### 3. Frontend

```bash
cd frontend
npm install                  # postinstall stages the Pyodide runtime
cp .env.example .env.local   # NEXT_PUBLIC_API_URL, if the API is not on :8000
npm run dev
```

The application is served at <http://localhost:3000>; the authenticated dashboard is at
`/academy`.

---

## Configuration

Backend settings are read from the environment; see `backend/.env.example` for the
annotated set and `backend/README.md` for the complete table.

| Variable | Default | Notes |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/windup` | Must use the `+asyncpg` driver |
| `SECRET_KEY` | dev placeholder | Signs JWTs; minimum 32 characters |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated; wildcards rejected outside development |
| `JUDGE_RUNNER` | `wasm` | `subprocess` does not sandbox and is development-only |
| `JUDGE_LANGUAGES` | all eight | Languages this deployment offers, in workbench order |

Configuration is validated at startup: the application refuses to boot outside
`ENV=development` with the committed development `SECRET_KEY`, a key shorter than 32
characters, or wildcard CORS.

The frontend takes a single variable, `NEXT_PUBLIC_API_URL` (default
`http://localhost:8000/api/v1`). All requests are made from the browser.

---

## Development

Frontend, from `frontend/`:

| Command | Description |
| --- | --- |
| `npm run dev` | Development server on :3000 |
| `npm run build` | Production build |
| `npm run start` | Serve the production build |
| `npm run lint` | ESLint — React Compiler rules are errors |
| `npx tsc --noEmit` | Typecheck without building |

Backend, from `backend/`:

| Command | Description |
| --- | --- |
| `uv run uvicorn app.main:app --reload` | API development server |
| `uv run python -m app.judge.worker` | Judge worker |
| `uv run alembic upgrade head` | Apply migrations |
| `uv run alembic revision --autogenerate -m "..."` | Generate a migration after model changes |
| `uv run python -m app.db.seed` | Seed zones, problems and achievements |
| `uv run pytest` | Test suite |
| `uv run ruff check .` | Lint |

Commits follow [Conventional Commits](https://www.conventionalcommits.org) with a scope,
for example `feat(backend): …`.

---

## Testing

```bash
cd backend
createdb windup_test          # or set TEST_DATABASE_URL
uv run pytest
uv run pytest tests/test_problems.py::test_name -x   # a single test
```

The suite runs against a dedicated database: the schema is created once per session and
tables are truncated between tests, so the development database is untouched.

Test coverage of note:

- **Catalogue integrity** — every problem's reference solution is graded against its own
  test cases through the real judging path, without a database. An incorrect expected
  value in a hidden case fails the build rather than surfacing to a user on a case they
  cannot see.
- **Cross-language equivalence** — reference solutions in each supported language are
  graded against the same hidden cases, verifying that language choice cannot change a
  verdict.
- **Concurrency** — payout settlement is exercised under concurrent workers to confirm
  that a solve is never paid twice or lost.

Tests that judge a non-Python language skip automatically when that language's WASI
artifact has not been fetched.

There is no frontend test runner.

---

## Repository layout

```
frontend/
  app/                # App Router; one directory per route
  components/
    academy/routes/   # client containers — state and data fetching
    academy/screens/  # presentational components
  lib/
    api.ts            # single API client; token storage and refresh
    runners/          # in-browser execution engines behind Run

backend/
  app/
    core/             # settings, security, gameplay constants
    api/v1/endpoints/ # one module per screen area
    services/         # leveling, streaks, achievements, duels, payout
    models/           # SQLAlchemy tables
    schemas/          # Pydantic request/response models
    db/seed_data/     # problem catalogue, one module per zone
    judge/            # language packs, sandboxed runner, grading, worker
  alembic/            # migrations
  scripts/            # artifact and toolchain fetchers
  tests/
```
