# Windup

**Windup Academy** — a secret training academy run by toys. Fix broken gadgets, climb the shelves, battle boss toys, and earn merit badges while mastering real data-structure and algorithm (DSA) interview patterns.

It reframes coding-interview prep as a playful quest: every DSA pattern is its own toy corner, hints live in tiered "help chests," and timed mock rounds are boss battles against giant toys.

## Features

- **Explorable quest map** — each DSA pattern is a themed toy corner (building blocks for arrays, a marble run for linked lists, a board game for graphs).
- **Tiered help chests** — a free pattern explainer, then locked hint / approach / solution chests; peek if you must, but forfeit the unaided bonus.
- **Boss battles** — timed mock-interview rounds against boss toys. Beat the clock before the Jack-in-the-Box springs.
- **Merit badges & streaks** — sticker badges, a wind-up charge meter, and a spinning-top streak to keep progress tangible.

## Tech stack

**Frontend**

- [Next.js](https://nextjs.org) 16 (App Router)
- React 19
- TypeScript 5
- Fonts: Fredoka + Nunito via `next/font`

**Backend**

- [FastAPI](https://fastapi.tiangolo.com) (async) + Uvicorn
- PostgreSQL via SQLAlchemy 2.0 (`asyncpg`) + Alembic
- Pydantic v2, JWT auth, bcrypt password hashing
- Managed with [`uv`](https://docs.astral.sh/uv/)

## Project structure

```
frontend/
  app/               # Next.js App Router
    page.tsx         # Landing + auth flow (with confetti)
    academy/         # Academy dashboard (quests, boss, achievements, …)
    layout.tsx       # Root layout, fonts, metadata
    globals.css
  components/         # Landing, Auth, Confetti, PushButton, academy/*

backend/
  app/
    main.py          # FastAPI app, CORS, /health
    core/            # settings, JWT + bcrypt
    db/              # engine, session, seed data
    models/          # SQLAlchemy tables
    schemas/         # Pydantic request/response models
    api/v1/endpoints # one module per screen area
    services/        # leveling, streaks, achievements, analytics
  alembic/           # migrations
  tests/
```

## Getting started

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the landing page; the Academy dashboard lives at `/academy`.

### Backend

```bash
cd backend
uv sync
cp .env.example .env                  # edit DATABASE_URL / SECRET_KEY
createdb windup                       # or: docker compose up -d db
uv run alembic upgrade head
uv run python -m app.db.seed --demo   # catalogue + demo toy
uv run uvicorn app.main:app --reload --port 8000
```

API docs at [http://localhost:8000/docs](http://localhost:8000/docs). Demo login:
`bramble@playroom.com` / `windup123`. See [`backend/README.md`](backend/README.md)
for the full endpoint reference and data model.

## Scripts

Run from the `frontend/` directory:

| Command         | Description                |
| --------------- | -------------------------- |
| `npm run dev`   | Start the dev server       |
| `npm run build` | Production build           |
| `npm run start` | Serve the production build |
| `npm run lint`  | Run ESLint                 |

Run from the `backend/` directory:

| Command                          | Description                  |
| -------------------------------- | ---------------------------- |
| `uv run uvicorn app.main:app --reload` | Start the API dev server |
| `uv run alembic upgrade head`    | Apply migrations             |
| `uv run python -m app.db.seed`   | Seed zones, problems, badges |
| `uv run pytest`                  | Run the test suite           |
| `uv run ruff check .`            | Lint                         |
