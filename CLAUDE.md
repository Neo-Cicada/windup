# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Windup Academy — a toy-themed DSA interview-prep app. Two independent applications in one repo:

- `frontend/` — Next.js 16 App Router + React 19 (TypeScript)
- `backend/` — FastAPI + PostgreSQL (async SQLAlchemy 2.0), managed with `uv`

The two halves are wired: every screen renders server data fetched through `frontend/lib/api.ts`, and the academy is gated behind a real session. `NEXT_PUBLIC_API_URL` points the client at the API (default `http://localhost:8000/api/v1`); both servers must be running for the app to do anything.

## Commands

### Frontend (`cd frontend`)

```bash
cp .env.example .env.local   # NEXT_PUBLIC_API_URL, if the API isn't on :8000
npm install            # postinstall copies the Pyodide runtime into public/pyodide/
npm run dev            # dev server on :3000  (landing at /, dashboard at /academy)
npm run build          # production build
npm run lint           # eslint — React Compiler rules are errors, see below
npx tsc --noEmit       # typecheck without building
```

There is no frontend test runner. `/academy` needs the backend up, a judge worker running, and a logged-in session.

The problem screen has two buttons and they are not the same thing. **Run** executes the visible examples in the browser via Pyodide in a Web Worker (`lib/pyodide.ts`, worker at `public/pyodide/runner.worker.js`) — instant, earns nothing, grades nothing, and keeps the great majority of executions off the server. **Submit** sends the code to the judge and is the only thing that decides whether a problem is solved. The ~11MB runtime is gitignored, copied in by `scripts/copy-pyodide.mjs`, and fetched only when a toy first presses Run.

### Backend (`cd backend`)

```bash
uv sync                                  # create .venv, install deps
./scripts/fetch_python_wasm.sh           # CPython-WASI build for the judge (20MB, gitignored)
docker compose up -d db                  # or: createdb windup
uv run alembic upgrade head
uv run python -m app.db.seed --demo      # catalogue + demo toy (bramble@playroom.com / windup123)
uv run uvicorn app.main:app --reload --port 8000   # docs at /docs, /health
uv run python -m app.judge.worker        # the judge — solving does nothing without it

uv run pytest                            # needs a windup_test DB (or TEST_DATABASE_URL)
uv run pytest tests/test_problems.py::test_name -x   # single test
uv run ruff check .                      # lint (E, F, I, UP, B; line-length 100)

uv run alembic revision --autogenerate -m "..."     # after changing models
```

Tests run against a throwaway database: the schema is created once per session and every table is `TRUNCATE`d between tests, so the dev database is never touched. `asyncio_mode = "auto"` — do not add `@pytest.mark.asyncio`. Use the `client`, `db`, `seeded`, `auth` and `judge` fixtures from `tests/conftest.py` (`auth` returns a ready Bearer header).

Because submitting is asynchronous, a test that wants a verdict has to run the judge itself: `judge.solve(slug)` submits, drains the queue and returns the settled result; `judge.submit(...)` / `judge.drain()` / `judge.result(id)` are there when the steps matter separately. The fixture uses `SubprocessRunner`, so the suite needs no wasm artifact; the wasm runner has its own parameterized tests that skip when `vendor/python.wasm` is absent.

## Backend architecture

Layering is `api/v1/endpoints/*` → `services/*` → `models/*`, with `schemas/*` (Pydantic v2) at the boundary. One endpoint module per frontend screen area; `api/v1/router.py` mounts them all under `/api/v1`.

- **Dependency aliases** live in `app/api/deps.py`: `DbSession`, `CurrentUser`, `CurrentProgress`. Endpoints take these `Annotated` types rather than calling `Depends` inline.
- **Transactions**: `get_db` yields a session that rolls back on exception; endpoints own their own `await db.commit()`.
- **Model registration**: `app/models/__init__.py` re-exports every model — a new table must be added there or it won't reach `Base.metadata` (breaking both Alembic autogenerate and the test schema).
- **Alembic runs synchronously** via `settings.sync_database_url` (strips `+asyncpg`). `alembic/versions/` is excluded from ruff.
- **Enums** are `StrEnum` in `app/models/enums.py` and are stored as their string values.

### The judge (`app/judge/`)

`harness.py` assembles the guest program, `runner.py` executes it, `grade.py` compares, `worker.py` is the claim loop. Every problem is called the same way — `_dump(entrypoint(*_build(args)))` — so a problem needing a `ListNode` defines it and overrides the adapters in its own `harness_preamble`, and the runner needs no per-problem branching.

The security property is that **expected values never enter the sandbox**: only arguments go in, and the host compares. Submitted code shares a process with the driver and can write anything to stdout, but without the expected values the only way to forge a pass is to emit correct answers.

`WasmRunner` (default) is CPython-on-WASI under wasmtime — fuel caps CPU, a store limit caps memory, and no preopened directory means no filesystem and no sockets. `SubprocessRunner` does **not** sandbox and refuses to be selected outside `ENV=development`.

Payout lives in `app/services/submissions.py::settle()`. Three things keep it correct and all three are load-bearing, because the deployment story is "run more workers": `settled_at` stops a retried job paying twice; a `SELECT … FOR UPDATE` on the toy's `progress` row serialises settlement per toy (without it, concurrent settlements clobber each other's counters and a solve disappears); and the already-paid probe tests for a previously *settled* run rather than any other passing run (without that, two unsettled passing runs each defer to the other and neither pays).

### Gameplay constants

Tuning numbers (`XP_SOLVE_UNAIDED`, `XP_MAX_GROWTH`, `BOSS_DURATION_SECONDS`, `DAILY_QUESTS`, `JUDGE_*`, …) live in `app/core/config.py` as settings, not as literals in endpoints.

The frontend no longer recomputes any of this: XP, levels, level names and streaks come back on the response to whatever caused them (`SubmissionResultOut.progress`, `DashboardOut` from `/me/wind-up`). `app/services/leveling.py` is the only implementation — don't reintroduce an optimistic copy in the client.

### Server-authoritative invariants

These are the load-bearing rules; several endpoints exist specifically to enforce them:

- **The server decides whether a submission passed.** `SubmissionIn` has no `status` field — the client cannot declare a verdict. `POST /problems/{slug}/submit` queues the code and returns `202`; a judge worker runs it and the client polls `GET /submissions/{id}`. Everything that used to fire off the submit response (confetti, XP, the boss round) now fires off the verdict.
- Hidden test cases never leave the server, exactly like locked chests. `ProblemDetailOut` carries only `example`-visibility cases plus a `hidden_test_count`. A failing *hidden* case reports its arguments and the toy's own output but withholds the expected value — otherwise the hidden tests become a lookup table.
- Locked help-chest tiers come back as `null` from `GET /problems/{slug}` — the server never ships a chest the user hasn't opened. Opening one records a `ChestUnlock`, which is what makes a later solve "aided" (base reward instead of double).
- Re-solving a problem pays nothing, which is also what stops old solves from clearing a boss rematch.
- Boss `complete` is not self-declared: it counts distinct problems solved *during that session* (submissions carrying its `boss_session_id` that paid out XP) and returns `409` naming the shortfall. The clock is computed server-side from the last resume, so refreshing or opening a second tab can't extend it.
- `POST /me/wind-up` is once per day, enforced by a unique constraint (see the `enforce_one_wind_up_per_day` migration).
- `PATCH /me` edits toy name and notification toggles only. Password and email changes re-authenticate with the current password.
- `Settings` refuses to boot outside `ENV=development` with the committed dev `SECRET_KEY`, a key under 32 chars, or wildcard CORS.

`XpEvent` is an append-only ledger — the weekly chart and the streak heatmap read from it rather than from counters.

See `backend/README.md` for the full endpoint table and data model.

## Frontend architecture

`app/page.tsx` is the landing + auth flow; `app/academy/page.tsx` is the entire dashboard — it owns the data fetching and switches between `components/academy/screens/*` via a `ScreenKey`. Screens stay presentational: they take props and callbacks. The one exception is `screens/Profile.tsx`, which owns its own form fields and returns them to the page on save.

### Data layer (`lib/`)

- `api.ts` — the only place that talks to the API. Holds the tokens, attaches the bearer header, and on a 401 for an authenticated request does a **single-flight** refresh and retries once; if that fails it clears the session and notifies `onSessionExpired` subscribers. A 401 with no token attached (a bad login) falls through so the backend's own message reaches the form. Tokens live in `localStorage` because the API is stateless bearer-only — this is the file to change if it ever grows an httpOnly-cookie flow.
- `auth.tsx` — `AuthProvider` (mounted in `app/layout.tsx`) with `status: "loading" | "authed" | "anon"`. A stored token is only a claim until `/me` confirms it.
- `useResource.ts` — `GET` a path into state, with `enabled` so a screen only fetches when it's open. `loading` is *derived* (a snapshot whose path doesn't match the requested one is a request in flight), not stored.
- `components/RequireAuth.tsx` — wraps the academy. Children never render until `/me` succeeds, so there's no flash of the dashboard.

The route gate is client-side; the real lock is that every endpoint except signup/login/refresh requires the bearer token, so the page shell is worthless without a session. Middleware can't gate it — the token is in `localStorage`, not a cookie.

### React Compiler constraints

The React Compiler is on, and `eslint-config-next` enforces its rules as **errors** — `npm run lint` will reject:

- `setState` called synchronously in an effect body. Set state from promise callbacks, intervals, or event handlers instead; where that's impossible, derive the value rather than storing it (see `useResource`, and the bootstrap in `auth.tsx` that routes both branches through a promise).
- Impure calls during render — `Date.now()` in the render path fails `react-hooks/purity`. The boss countdown ticks from an interval for this reason.
- Hand-written `useCallback`/`useMemo` whose inferred deps don't match (`react-hooks/preserve-manual-memoization`). Plain functions in a component body are fine and preferred; the compiler memoizes them.

### Styling

Styling is **inline style objects**, not CSS modules or a framework. `app/globals.css` carries only resets, base typography, and the `@keyframes` (`cfall`, `spin`, `wob`, `floaty`, `pop`, `tick`) that components reference by name. Shared tokens (`FREDOKA`, `DARK`, `MONO`, `NAV`, `TITLES`) and pure presentation helpers (`buildShelves`, `pegColor`, `streakColors`, `buildPodium`) come from `components/academy/data.ts`; fonts are wired as CSS variables in `app/layout.tsx` via `next/font`.

**Next.js 16 caveat** (`frontend/AGENTS.md`, aliased by `frontend/CLAUDE.md`): this version has breaking changes versus older Next.js — APIs, conventions, and file structure may differ from what you expect. Read the relevant guide in `frontend/node_modules/next/dist/docs/` before writing App Router code, and heed deprecation notices.

## Conventions

- Commits follow Conventional Commits with a scope: `feat(backend): …`, `test(backend): …`, `docs: …`.
- User-facing API messages stay in the toy voice ("Sprocket doesn't recognise that key", "That toy isn't on any shelf"). Match the surrounding tone rather than writing generic errors.
- Domain vocabulary maps to plain terms: charge = XP, shelf level = level, toy = user, help chest = hint tier, boss battle = timed mock round, merit sash = achievements, shelf of fame = leaderboard.
