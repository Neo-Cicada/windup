# Windup Academy — Backend

FastAPI + PostgreSQL API for the Windup Academy frontend. Every screen in `frontend/`
has an endpoint behind it: auth, the quest map, problems and their tiered help chests,
boss battles, merit badges, analytics, the shelf of fame, and account settings.

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
| `GET` | `/problems/{slug}` | Detail. **Locked tiers come back as `null`** — the server never leaks a chest you haven't opened |
| `POST` | `/problems/{slug}/chests/{tier}` | Open `hint` \| `approach` \| `solution`; forfeits the unaided bonus |
| `POST` | `/problems/{slug}/submit` | Run & Submit: awards charge, updates the quest card, checks badges |

Scoring matches the frontend: an unaided solve pays double the problem's reward
(120 for a 60-point toy), an aided solve pays the base, and re-solving pays nothing.

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

### Merit sash, analytics, shelf of fame

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/achievements` | All 12 badges with earned state and `"3/12"` label |
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
- **Zone** → **Problem** (1-n): a toy corner and its problems, help text on the problem
- **ChestUnlock**: which tiers a toy has opened per problem — this is what makes a
  solve "aided"
- **Submission**: every Run & Submit, with the charge it paid out
- **DailyQuest**: today's three cards
- **XpEvent**: append-only charge ledger driving the weekly chart and streak heatmap
- **Achievement** / **UserAchievement**: the merit sash
- **BossSession**: timed mock rounds

## The frontend

The Next.js app talks to this API through `frontend/lib/api.ts`, which stores the token
pair, attaches the bearer header, and refreshes once on a 401 before giving up on the
session. Point it at a different host with `NEXT_PUBLIC_API_URL` (default
`http://localhost:8000/api/v1`), and keep this origin in `CORS_ORIGINS`.

Every screen hydrates from the endpoint listed beside it above — `GET /dashboard` fills
the whole Playroom in one round trip — and the client no longer computes charge, levels
or streaks itself: it renders the `progress` block that comes back with each mutation.
