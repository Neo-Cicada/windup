# Windup Academy — Backend

FastAPI + PostgreSQL API for the Windup Academy frontend. Every screen in `frontend/`
has an endpoint behind it: auth, the quest map, problems and their tiered help chests,
boss battles, duels, merit badges, analytics, the shelf of fame, and account settings.

## Stack

- **FastAPI** (async) + **Uvicorn**
- **PostgreSQL** via **SQLAlchemy 2.0** (async, `asyncpg`) and **Alembic**
- **Pydantic v2** for schemas and settings
- **JWT** access/refresh tokens (`pyjwt`), passwords hashed with **bcrypt**
- **pytest** + **httpx** for tests, **ruff** for linting
- Managed with [`uv`](https://docs.astral.sh/uv/)

## Getting started

```bash
cd backend
uv sync                       # create .venv and install
cp .env.example .env          # then edit DATABASE_URL / SECRET_KEY

createdb windup               # or: docker compose up -d db
uv run alembic upgrade head   # create the schema
uv run python -m app.db.seed --demo   # zones, problems, badges + demo toy

uv run uvicorn app.main:app --reload --port 8000
```

- Interactive docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>
- Demo login: `bramble@playroom.com` / `windup123`

### Tests

```bash
createdb windup_test          # or set TEST_DATABASE_URL
uv run pytest                 # 34 tests
uv run ruff check .
```

The suite creates the schema once and truncates between tests, so it never touches
your development database.

## Configuration

All settings come from the environment (see `.env.example`):

| Variable | Default | Notes |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/windup` | Must use the `+asyncpg` driver |
| `SECRET_KEY` | dev placeholder | **Change in production** — signs JWTs |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `720` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated |
| `TEST_DATABASE_URL` | `…/windup_test` | Tests only |

Gameplay constants (`XP_SOLVE_UNAIDED`, `BOSS_DURATION_SECONDS`, …) also live in
`app/core/config.py` so tuning doesn't need a code change.

## API

All routes are under `/api/v1` and require `Authorization: Bearer <access_token>`
except signup, login, refresh, and `/health`.

### Auth — `components/Auth.tsx`, `app/page.tsx`

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/auth/signup` | Unbox a new toy; returns tokens + user |
| `POST` | `/auth/login` | Log in |
| `POST` | `/auth/refresh` | Trade a refresh token for a new pair |
| `POST` | `/auth/logout` | Client-side token drop (symmetry with the UI) |

### Playroom — `screens/Dashboard.tsx`, `Topbar.tsx`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/dashboard` | Whole home screen in one call: toy, progress, quests, badge count, rank, Sprocket's line |
| `GET` | `/quests/today` | Today's quest cards (3/day free, 5 on paid) |
| `PATCH` | `/quests/{id}` | Nudge a quest's progress bar |
| `POST` | `/me/wind-up` | The topbar wind-up key (+40 charge). **Once per day** — `wind_up_available` on `/dashboard` says whether it's still claimable |
| `GET` | `/me/progress` | Charge, level, streak, coins, unaided rate, readiness |

### Quest map — `screens/QuestMap.tsx`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/zones` | Every toy corner with `done`/`total` |
| `GET` | `/zones/{slug}/problems` | That corner's problems |

### Problems & help chests — `screens/ProblemView.tsx`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/problems` | List; filter by `zone`, `difficulty` |
| `GET` | `/problems/{slug}` | Detail, including a bench per language it can be solved in. **Locked tiers come back as `null`** — the server never leaks a chest you haven't opened |
| `GET` | `/languages` | What this deployment can judge |
| `POST` | `/problems/{slug}/chests/{tier}` | Open `hint` \| `approach` \| `solution`; forfeits the unaided bonus |
| `POST` | `/problems/{slug}/submit` | Queue the code for judging. **202**, returns a submission id — it does not run anything. A language the problem doesn't offer is a **400** |
| `GET` | `/submissions/{id}` | Poll for the verdict. Verdict fields are `null` until the judge has ruled |

Scoring matches the frontend: an unaided solve pays double the problem's reward
(120 for a 60-point toy), an aided solve pays the base, and re-solving pays nothing.

Submitting is asynchronous, and `SubmissionIn` has no `status` field — the client
cannot declare its own verdict. See **The judge** below.

### Boss battles — `screens/BossBattle.tsx`

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/boss/sessions` | Start a 15-minute round |
| `GET` | `/boss/current` | The in-flight fight, with server-authoritative time left |
| `POST` | `/boss/sessions/{id}` | `{"action": "pause"\|"resume"\|"complete"\|"abandon"}` |
| `GET` | `/boss/sessions` | Recent fights |

The clock is kept server-side: `remaining_seconds` and `time_label` are computed
from when the fight was last resumed, so a refresh or a second tab can't cheat it.
Winning pays 300 charge plus a speed bonus of up to 150.

`complete` is **not** a self-declared win. It counts the distinct problems actually
solved during that fight — submissions carrying the session's `boss_session_id` that
paid out XP — and returns `409` naming the shortfall until every round is cleared.
Because a re-solve pays nothing, old solves can't be recycled to clear a rematch.

### Duels — `screens/DuelArena.tsx`

Two toys, the same problems, one clock, first to fix them all.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/duels` | Open a challenge; returns a six-letter code to share |
| `GET` | `/duels/current` | The duel this toy is in, if any |
| `GET` | `/duels/{id}` | The ~2s poll. `404` for anyone who isn't one of the two |
| `GET` | `/duels/by-code/{code}` | Invite preview. Deliberately cannot carry the problems |
| `POST` | `/duels/by-code/{code}/join` | Accept — picks the rounds and starts the clock |
| `POST` | `/duels/{id}/actions` | `{"action": "forfeit"\|"cancel"}` |
| `GET` | `/duels` | Recent duels |

Everything is serialised from the caller's own side — `you` and `them`, never host and
opponent — and the server owns the poll cadence through `poll_after_ms` (2s racing, 5s
waiting, 0 once it's over).

Three things are worth knowing:

- **The problem set doesn't exist until someone joins.** `duel_rounds` rows are written
  in the transaction that starts the clock, which is both the reveal mechanism (a
  waiting duel has no rounds to leak) and the first moment both solve histories are
  known — the set is filtered against the pair, preferring problems neither has fixed.
- **A round clears on any passed submission tagged into the duel for a problem in its
  set** — unlike the boss, which demands a first-time solve. That rule would make a
  race silently unwinnable for whoever had solved one of the problems before.
- **The winner is decided by whichever poll gets there first**, from committed
  `judged_at` timestamps, under a conditional `UPDATE ... WHERE status = 'active'`. The
  decision is pure, so both players compute the same answer; the guard only picks who
  writes it down. `settle()` is deliberately not involved.

Winning a clean sweep pays 250 plus a speed bonus up to 100, plus 40 per round cleared;
leading when the clock runs out wins without the speed bonus; a forfeit hands the other
toy 60. Duel bonuses are capped per day (`DUEL_DAILY_BONUS_CAP`), which is what bounds
two accounts duelling each other on a loop.

### Merit sash, analytics, shelf of fame

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/achievements` | All 13 badges with earned state and `"3/13"` label |
| `GET` | `/analytics` | Weekly charge chart, pattern pegboard, unaided gauge, streak grid |
| `GET` | `/analytics/xp-history` | Charge per day (`?days=`) |
| `GET` | `/analytics/coverage` | Per-pattern level 1-5 |
| `GET` | `/analytics/streak` | 36 activity cells for the 3x12 heatmap |
| `GET` | `/leaderboard` | Ranked toys, podium order (2nd, 1st, 3rd), your rank |

### Account — `screens/Profile.tsx`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/me` | Current toy |
| `PATCH` | `/me` | "Save account": toy name and notification toggles only |
| `POST` | `/me/password` | Password change, re-authenticated |
| `POST` | `/me/email` | Email change, re-authenticated |

Credentials are deliberately **not** editable through `PATCH /me` — both take the
current password, so a leaked access token alone can't lock the owner out.

## Layout

```
backend/
  app/
    main.py              # app factory, CORS, /health
    core/                # settings, JWT + bcrypt
    db/                  # engine, session, Base, seed data
    models/              # SQLAlchemy tables
    schemas/             # Pydantic request/response models
    api/v1/endpoints/    # one module per screen area
    services/            # leveling, streaks, achievements, analytics
  alembic/               # migrations
  tests/
```

## Data model

- **User** → **Progress** (1-1): charge, shelf level, streak, coins, counters
- **Zone** → **Problem** (1-n): a toy corner and its problems, help text on the problem.
  The seeded catalogue is 19 corners of 5 problems each, one corner per topic on
  the NeetCode roadmap plus Toy Kitchen for SQL, in roadmap order
- **ChestUnlock**: which tiers a toy has opened per problem — this is what makes a
  solve "aided"
- **ProblemTest**: the graded cases. `example` ones ship to the client for the
  in-browser Run button; `hidden` ones never leave the server. Shared by every
  language a problem offers
- **ProblemLanguage**: one bench — the stub, preamble and entrypoint for one
  language of one problem. Absent for the problem's own `language`, which needs
  no row
- **Submission**: every submit, its place in the judge queue, its verdict, and the
  charge it paid out. Doubles as the queue table
- **DailyQuest**: today's three cards
- **XpEvent**: append-only charge ledger driving the weekly chart and streak heatmap
- **Achievement** / **UserAchievement**: the merit sash
- **BossSession**: timed mock rounds
- **Duel** / **DuelRound**: a head-to-head race and its problem set. The rounds are
  written at join time, not at create time

## The judge

Submitted code is executed, and the server decides whether it passed. Two
processes are involved and neither of them is the one serving requests:

```bash
./scripts/fetch_language_wasm.sh          # once: every language's WASI build (gitignored)
./scripts/fetch_toolchains.sh             # once: the C++/Rust/Go compilers, if you want them
uv run python -m app.judge.worker         # the judge; run as many as you need
uv run python -m app.judge.worker --once  # drain the queue and exit
```

Only worker hosts need any of that — the API compiles and runs nothing. A
language whose artifact or toolchain is missing should be left out of
`JUDGE_LANGUAGES`; a worker refuses to start rather than discover it later.

`POST /submit` validates and inserts a `pending` submission, then returns. Workers
claim rows with `FOR UPDATE SKIP LOCKED` — which is why this needs no broker beyond
the Postgres already here — run them, write the verdict, and settle the payout.
**The API never executes submitted code**: one toy's infinite loop burns a worker,
not the event loop serving everyone else.

`app/judge/`:

- `languages/*.py` assemble `default adapters + the problem's preamble + the toy's
  code + a driver`. Every problem is called the same way, `_dump(entrypoint(*_build(args)))`,
  so nothing needs per-problem branching; a problem that needs a `ListNode` defines
  it, and overrides `_build`/`_dump`, in its `harness_preamble`. One pack per
  language, all producing the same wire format (see below).
- `harness.py` is what is left once assembly is per-language: the case payload in,
  and the JSONL read back out.
- `bench.py` answers which languages a given problem offers, and with what stub and
  preamble. `signature.py` is the type language those stubs are generated from.
- `runner.py` runs it. `WasmRunner` (default) executes an interpreter-on-WASI under
  wasmtime: fuel metering caps CPU, a store memory limit caps allocation, and
  because no directory is ever preopened the guest has no filesystem and no
  sockets. It compiles every offered language's module at startup, so a missing
  artifact refuses to boot with the command to fetch it rather than failing a
  submission later. `SubprocessRunner` is a development fallback that does **not**
  sandbox, is Python-only, and refuses to be selected outside `ENV=development`.
- `grade.py` compares. **Expected values never enter the sandbox** — only arguments
  go in, and the host does the comparison. Submitted code shares a process with the
  driver and can print whatever it likes, but with no expected values in reach the
  only way to forge a pass is to emit correct answers, which is solving the problem.
- `worker.py` is the loop. `abandon_exhausted` sweeps runs whose worker died on
  their final attempt — `claim_batch` skips rows at the attempt ceiling, so
  without the sweep they would stay `running` forever.

`settle()` takes a `SELECT … FOR UPDATE` on the toy's `progress` row before it
touches anything. Every step after that is a read-modify-write on shared state —
the XP counters, `solved_count`, the streak, and the probe deciding whether the
solve pays — so two workers settling for one toy without the lock lose a solve
from the counters while both submissions tell the client they paid. That probe
also asks whether a previous run has been *settled*, not merely whether another
passing run exists: two unsettled passing runs would otherwise each defer to the
other and neither would pay.

Tuning lives in `app/core/config.py` as `JUDGE_*` settings, not as literals.
`JUDGE_FUEL` is an instruction budget, not a clock: CPython's startup burns
0.24G, the heaviest seeded problem 1.7G, and the default 8G trips a runaway loop
in about half a second. It is a *default* — a pack whose interpreter is cheaper
sets its own, and QuickJS does (3.1M startup, 3G budget, runaway in ~170ms).

A problem with `graded=False` skips the judge and settles inline on the honour
system. Nothing in the seeded catalogue needs that today.

### More than one language

| language | interpreter | browser Run | notes |
| --- | --- | --- | --- |
| Python | CPython-WASI | Pyodide | the default; 8G fuel |
| JavaScript | QuickJS-NG-WASI | a plain Worker, no download | 3G fuel; `-C` forces a classic script so a preamble may redefine the adapters |
| Ruby | CRuby-WASI | — | 6G fuel; 0.54G of it is booting the interpreter and requiring `json` |
| PHP | php-cgi-WASI | — | the awkward one, see `languages/php.py` |
| SQL | SQLite, inside CPython-WASI | Pyodide's bundled `sqlite3` | no artifact of its own on either side |
| C++ | wasi-sdk clang → wasm | — | ~1s to build |
| Rust | `rustc --target wasm32-wasip1` | — | ~1s; plain rustc, no cargo and no crates |
| Go | TinyGo → wasm | — | ~3s, the slowest of the three |

SQL is the one that isn't a function call. It has no entrypoint and no
signature; its `harness_preamble` is the schema, each case's `args` are the rows
to put in the tables (`{"table": ..., "rows": [[...]]}`), and `expected` is the
result set. The pack emits a *Python* program and hands it to the Python pack,
so the driver, the wire format and the grader are all the ones already there.

No Lua: the available builds are single-maintainer rebuilds rather than a
first-party release, and Lua ships no JSON in its standard library, so its driver
would need a hand-written serialiser — where a bug is a wrong verdict rather than
an error.

A toy picks the language per submission, and adding one changes nothing about
grading:

- **One set of cases grades every language.** `args_json` / `expected_json` are
  plain JSON compared on the host, so `grade.py` has no per-language code in it.
- Every pack's driver speaks the same wire format — `{"tests":[{ordinal,args}]}`
  in on stdin, one `{ordinal,actual,stdout,error}` JSON object per line out — so
  the security property above is argued once, not once per language.
- Every interpreter takes its program on **argv** (`-c`, `-e`), which is how the
  guest keeps having no filesystem.
- `languages/__init__.py` is the registry; `JUDGE_LANGUAGES` is what a deployment
  offers. `GET /languages` reports the latter.
- A problem offers its own `language` plus whatever `problem_languages` rows it
  has. `problems.signature_json` describes the *call* — not the JSON, since
  `_build` may fold several JSON values into one argument — and every pack
  generates its starter stub from it. A bench row exists to override that,
  usually with a structural preamble, because a preamble is source code and is
  never inherited across languages.

#### The compiled three

C++, Rust and Go have no interpreter to hand a program to, so `compile.py`
builds them on the host first and the sandbox instantiates *that* module. The
compiler is the one place untrusted input touches the host, so it gets rlimits,
a scratch directory, no network and a clock of its own; a build failure is a
verdict carrying the compiler's own diagnostics, not a crash.

They also skip JSON entirely. Parsing a payload in a statically typed language
needs a variant type and a parser — hundreds of lines where a bug is a *wrong
verdict* — so instead the host renders each case's arguments as **typed
literals** straight into the source (the whole catalogue carries 135 bytes of
arguments at most). The compiler then type-checks every call, and the only
serialising left is the return value, whose type the signature already gave.

Two things follow, and both are deliberate:

- **The toy's own prints are not handed back.** WASI gives the guest no pipe and
  no filesystem to redirect stdout into, so a `printf` lands on the result
  stream and `parse_results` discards it as noise. Nothing grades wrongly; there
  is simply no debugging output on the way back.
- **They do not offer the structural problems** — the ten in Marble Run and
  Branching Mobile that hand the entrypoint a chute or a mobile. Rendering
  literals needs to know what the raw JSON holds, which `signature.args` can
  express, but `call_for` can only feed a *single* argument through `_build`, so
  anything taking two lists is out on its own. Each would also need its node type
  and `_build` written three more times, and linked-list-cycle cannot be
  expressed with Rust's `Box` at all: a cyclic list needs `Rc<RefCell<..>>`, a
  different type for the toy to write against.

## The frontend

The Next.js app talks to this API through `frontend/lib/api.ts`, which stores the token
pair, attaches the bearer header, and refreshes once on a 401 before giving up on the
session. Point it at a different host with `NEXT_PUBLIC_API_URL` (default
`http://localhost:8000/api/v1`), and keep this origin in `CORS_ORIGINS`.

Every screen hydrates from the endpoint listed beside it above — `GET /dashboard` fills
the whole Playroom in one round trip — and the client no longer computes charge, levels
or streaks itself: it renders the `progress` block that comes back with each mutation.
