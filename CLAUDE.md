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

The problem screen has two buttons and they are not the same thing. **Run** executes the visible examples in the browser — instant, earns nothing, grades nothing, and keeps the great majority of executions off the server. **Submit** sends the code to the judge and is the only thing that decides whether a problem is solved.

`lib/runners/` holds one browser engine per language it is cheap to run locally: Python through Pyodide (`public/pyodide/runner.worker.js`; the ~11MB runtime is gitignored, copied in by `scripts/copy-pyodide.mjs`, and fetched only when a toy first presses Run) and JavaScript through a plain Worker (`public/runners/js.worker.js`, which downloads nothing at all). A language with no entry in that registry simply has no Run button — `runs_in_browser` on the problem payload is what the UI asks.

### Backend (`cd backend`)

```bash
uv sync                                  # create .venv, install deps (Python >= 3.12)
cp .env.example .env                     # DATABASE_URL / SECRET_KEY / CORS_ORIGINS / JUDGE_LANGUAGES
./scripts/fetch_language_wasm.sh         # every language's WASI build (gitignored)
./scripts/fetch_language_wasm.sh javascript   # or just one
./scripts/fetch_toolchains.sh            # the C++/Rust/Go compilers, if you want them
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

`languages/` assembles the guest program, `runner.py` executes it, `grade.py` compares, `worker.py` is the claim loop. Every problem is called the same way — `_dump(entrypoint(*_build(args)))` — so a problem needing a `ListNode` defines it and overrides the adapters in its own `harness_preamble`, and the runner needs no per-problem branching.

The security property is that **expected values never enter the sandbox**: only arguments go in, and the host compares. Submitted code shares a process with the driver and can write anything to stdout, but without the expected values the only way to forge a pass is to emit correct answers.

`WasmRunner` (default) runs an interpreter-on-WASI under wasmtime — fuel caps CPU, a store limit caps memory, and no preopened directory means no filesystem and no sockets. It compiles every offered language's module at startup, so a missing artifact is a refusal to boot with the fetch command, not a failed submission an hour later. `SubprocessRunner` does **not** sandbox, is Python-only, and refuses to be selected outside `ENV=development`.

#### Languages

A toy picks the language per submission, and the judge is built so that adding one changes nothing about grading:

- **One set of test cases grades every language.** `args_json` / `expected_json` are plain JSON compared on the host, so `grade.py` cannot tell which language produced a result — and has no per-language code in it at all.
- **A language pack (`languages/*.py`) owns one thing**: turning code into a program, plus the `RunnerSpec` naming which wasm to instantiate and with what argv. Every pack's driver speaks the same wire format — `{"tests":[{ordinal,args}]}` in on stdin, one `{ordinal,actual,stdout,error}` JSON object per line out — which is what makes the security property hold once rather than per language.
- Every interpreter takes its program on **argv** (`-c`, `-e`), which is how the guest keeps having no filesystem.
- **`languages/__init__.py` is the registry**; `settings.JUDGE_LANGUAGES` is what a deployment actually offers. Registered and offered are different questions — a pack can exist while its artifact hasn't been fetched. Today: Python, JavaScript, Ruby, PHP, SQL.
- **SQL is not a function call**, so its pack ignores the entrypoint and signature: the preamble is the schema, a case's `args` are the rows to load, and `expected` is the result set. It emits a *Python* program using `sqlite3` and hands it to the Python pack, which is why it needs no artifact on either side — Pyodide bundles `sqlite3` too, so Run works in the browser with no extra download.
- **C++, Rust and Go are compiled first** (`compile.py`, `languages/compiled.py`), on the host, into a wasm module the same sandbox then runs. They parse no JSON: the host renders each case's arguments as typed literals into the source, so the compiler type-checks every call and only the return value needs serialising. Consequences: the toy's own prints are discarded rather than handed back (WASI offers nothing to redirect stdout into), and they don't offer the three structural problems (a cyclic linked list can't be expressed with Rust's `Box`). Toolchains are a worker-host prerequisite — `scripts/fetch_toolchains.sh`.
- Each pack is shaped by its interpreter's quirks and those are documented where they bite: JavaScript needs `-C` so a preamble may redefine `_build`; PHP cannot redeclare a function at all, so its adapters come *last* and stand down, and it has no argv door so its program travels on stdin with the cases inside it.
- Fuel is **per pack**. 8G is tuned to CPython (0.24G of it is interpreter startup) and is wrong for anything else; QuickJS starts in 3.1M and gets 3G.

`bench.py` answers which languages a *problem* offers. The default (`problems.language`) is always offered, since the problem's own `starter_code` and `harness_preamble` were written for it; anything else needs a `problem_languages` row. A preamble is source code, so it is never inherited across languages — only the default's comes from the problem itself.

`signature.py` holds the small type language (`int`, `list<int>`, `matrix<string>`, `listnode`, `null<T>`, …) that `problems.signature_json` is written in. It describes the **call**, not the JSON: linked-list-cycle's cases hold two values that `_build` folds into one `head`, so its signature has one param. Packs generate starter stubs from it, which is what stops per-submission language choice from meaning hundreds of hand-written stubs — a bench row only exists to override that, usually with a structural preamble.

Payout lives in `app/services/submissions.py::settle()`. Three things keep it correct and all three are load-bearing, because the deployment story is "run more workers": `settled_at` stops a retried job paying twice; a `SELECT … FOR UPDATE` on the toy's `progress` row serialises settlement per toy (without it, concurrent settlements clobber each other's counters and a solve disappears); and the already-paid probe tests for a previously *settled* run rather than any other passing run (without that, two unsettled passing runs each defer to the other and neither pays).

### Gameplay constants

Tuning numbers (`XP_SOLVE_UNAIDED`, `XP_MAX_GROWTH`, `BOSS_DURATION_SECONDS`, `DAILY_QUESTS`, `JUDGE_*`, …) live in `app/core/config.py` as settings, not as literals in endpoints.

The frontend no longer recomputes any of this: XP, levels, level names and streaks come back on the response to whatever caused them (`SubmissionResultOut.progress`, `DashboardOut` from `/me/wind-up`). `app/services/leveling.py` is the only implementation — don't reintroduce an optimistic copy in the client.

### Server-authoritative invariants

These are the load-bearing rules; several endpoints exist specifically to enforce them:

- **The server decides whether a submission passed.** `SubmissionIn` has no `status` field — the client cannot declare a verdict. `POST /problems/{slug}/submit` queues the code and returns `202`; a judge worker runs it and the client polls `GET /submissions/{id}`. Everything that used to fire off the submit response (confetti, XP, the boss round) now fires off the verdict.
- Hidden test cases never leave the server, exactly like locked chests. `ProblemDetailOut` carries only `example`-visibility cases plus a `hidden_test_count`. A failing *hidden* case reports its arguments and the toy's own output but withholds the expected value — otherwise the hidden tests become a lookup table.
- **The problem decides which languages it can be solved in.** `ProblemDetailOut.languages` is the list, and submitting in anything else is a `400` — the client cannot invent a bench, and the verdict names the language that produced it.
- Locked help-chest tiers come back as `null` from `GET /problems/{slug}` — the server never ships a chest the user hasn't opened. Opening one records a `ChestUnlock`, which is what makes a later solve "aided" (base reward instead of double).
- Re-solving a problem pays nothing, which is also what stops old solves from clearing a boss rematch.
- Boss `complete` is not self-declared: it counts distinct problems solved *during that session* (submissions carrying its `boss_session_id` that paid out XP) and returns `409` naming the shortfall. The clock is computed server-side from the last resume, so refreshing or opening a second tab can't extend it.
- `POST /me/wind-up` is once per day, enforced by a unique constraint (see the `enforce_one_wind_up_per_day` migration).
- `PATCH /me` edits toy name and notification toggles only. Password and email changes re-authenticate with the current password.
- `Settings` refuses to boot outside `ENV=development` with the committed dev `SECRET_KEY`, a key under 32 chars, or wildcard CORS.

`XpEvent` is an append-only ledger — the weekly chart and the streak heatmap read from it rather than from counters.

Forgetting to start the worker is the likeliest way to break the academy, so it is diagnosed rather than left to look like a slow judge: a submission unclaimed for `JUDGE_STALL_AFTER_SECONDS` comes back from `GET /submissions/{id}` with `stalled: true` and an explanatory `sprocket_message`, and the client surfaces that instead of waiting out its own deadline.

See `backend/README.md` for the full endpoint table and data model.

## Frontend architecture

Every screen is a real URL. `/` is the pitch, `/login` and `/signup` the forms (both render `AuthRoute` with a different `mode`); the dashboard is nine routes under `/academy`:

| route | screen |
| --- | --- |
| `/academy` | Playroom |
| `/academy/quests` | Quest Map (`?zone=<slug>` opens a corner) |
| `/academy/problem` | redirects to today's first quest |
| `/academy/problem/[slug]` | the workbench |
| `/academy/boss` | Boss Battle |
| `/academy/achievements` · `/academy/analytics` · `/academy/leaderboard` · `/academy/profile` | the rest |

Each `page.tsx` is a server shell that exports `metadata` and renders one client container from `components/academy/routes/*`; the containers own the screen's own state and fetching, and `components/academy/screens/*` stay presentational — props and callbacks only. The exception is `screens/Profile.tsx`, which owns its own form fields and returns them to `ProfileRoute` on save.

The three public routes follow the same container/presentational split one level up — `LandingRoute`/`Landing`, `AuthRoute`/`Auth` — and both containers bounce an already-authed visitor to `/academy`. They draw from `components/data.ts` and `components/publicBg.ts`, which are **not** `components/academy/data.ts`; the two `data.ts` files are unrelated and both export `FREDOKA`.

`app/academy/layout.tsx` renders `AcademyShell` — `RequireAuth`, then `AcademyProvider`, then the sidebar, topbar and confetti. **The layout doesn't unmount as you move between screens, and that's load-bearing.** `AcademyProvider` (`useAcademy()`) owns everything shared: the `/dashboard` and `/analytics/streak` resources behind the topbar, the wind-up mutation, Sprocket's line, confetti, and the boss fight (`useBossFight`). So a leaf calling `dashboard.reload()` after a solve still moves the topbar, and a judge poll that settles after you've wandered off still pays out and throws its confetti.

The boss fight in particular *must* live there: a submission only counts towards a round if it carries the running session's id, and that id is read from the problem route. `/boss/current` is fetched on provider mount rather than when the boss screen opens, because a bookmarked problem link is a normal way in.

`NAV` in `components/academy/data.ts` is the single source of truth for the sidebar — `href`, `label` (the button) and `title` (the topbar). `isNavActive` is what keeps "Problem" lit on `/academy/problem/two-sum`; `titleForPath` feeds the topbar. Unsaved workbench code is kept per slug *and language* in `sessionStorage` (`components/academy/drafts.ts`), since the editor unmounts when you leave its route and switching benches to compare two stubs should not throw either attempt away.

### Data layer (`lib/`)

- `api.ts` — the only place that talks to the API. Holds the tokens, attaches the bearer header, and on a 401 for an authenticated request does a **single-flight** refresh and retries once; if that fails it clears the session and notifies `onSessionExpired` subscribers. A 401 with no token attached (a bad login) falls through so the backend's own message reaches the form. Tokens live in `localStorage` because the API is stateless bearer-only — this is the file to change if it ever grows an httpOnly-cookie flow.
- `auth.tsx` — `AuthProvider` (mounted in `app/layout.tsx`) with `status: "loading" | "authed" | "anon"`. A stored token is only a claim until `/me` confirms it.
- `useResource.ts` — `GET` a path into state. `loading` is *derived* (a snapshot whose path doesn't match the requested one is a request in flight), not stored. Routing made the `enabled` flag mostly redundant — a route container only mounts on its own route — but it's still there for the zone problems, which depend on `?zone=`.
- `types.ts` — hand-mirrors `backend/app/schemas`, field name for field name, so a schema change needs a matching edit here. It also owns `TERMINAL_STATUSES`, which is what `components/academy/pollForVerdict.ts` polls against (backing off to a 2s ceiling, giving up at 45s, and short-circuiting on `stalled`).
- `components/RequireAuth.tsx` — mounted in `app/academy/layout.tsx`, so one gate covers all nine routes. Children never render until `/me` succeeds, so there's no flash of the dashboard.

The route gate is client-side; the real lock is that every endpoint except signup/login/refresh requires the bearer token, so the page shell is worthless without a session. Middleware can't gate it — the token is in `localStorage`, not a cookie.

### React Compiler constraints

The React Compiler is on, and `eslint-config-next` enforces its rules as **errors** — `npm run lint` will reject:

- `setState` called synchronously in an effect body. Set state from promise callbacks, intervals, or event handlers instead; where that's impossible, derive the value rather than storing it (see `useResource`, and the bootstrap in `auth.tsx` that routes both branches through a promise).
- Impure calls during render — `Date.now()` in the render path fails `react-hooks/purity`. The boss countdown ticks from an interval for this reason.
- Hand-written `useCallback`/`useMemo` whose inferred deps don't match (`react-hooks/preserve-manual-memoization`). Plain functions in a component body are fine and preferred; the compiler memoizes them.

### Styling

Styling is **inline style objects**, not CSS modules or a framework. `app/globals.css` carries only resets, base typography, and the `@keyframes` (`cfall`, `spin`, `wob`, `floaty`, `pop`, `tick`) that components reference by name. Shared tokens (`FREDOKA`, `DARK`, `MONO`, `NAV`) and pure presentation helpers (`buildShelves`, `pegColor`, `streakColors`, `buildPodium`) come from `components/academy/data.ts`; fonts are wired as CSS variables in `app/layout.tsx` via `next/font`.

**Next.js 16 caveat** (`frontend/AGENTS.md`, aliased by `frontend/CLAUDE.md`): this version has breaking changes versus older Next.js — APIs, conventions, and file structure may differ from what you expect. Read the relevant guide in `frontend/node_modules/next/dist/docs/` before writing App Router code, and heed deprecation notices.

## Conventions

- Commits follow Conventional Commits with a scope: `feat(backend): …`, `test(backend): …`, `docs: …`.
- User-facing API messages stay in the toy voice ("Sprocket doesn't recognise that key", "That toy isn't on any shelf"). Match the surrounding tone rather than writing generic errors.
- Domain vocabulary maps to plain terms: charge = XP, shelf level = level, toy = user, help chest = hint tier, boss battle = timed mock round, merit sash = achievements, shelf of fame = leaderboard.
