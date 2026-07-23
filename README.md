# Windup

**Windup Academy** — a secret training academy run by toys. Fix broken gadgets, climb the shelves, battle boss toys, and earn merit badges while mastering real data-structure and algorithm (DSA) interview patterns.

It reframes coding-interview prep as a playful quest: every DSA pattern is its own toy corner, hints live in tiered "help chests," and timed mock rounds are boss battles against giant toys.

## Features

- **Explorable quest map** — each DSA pattern is a themed toy corner (building blocks for arrays, a marble run for linked lists, a board game for graphs).
- **Tiered help chests** — a free pattern explainer, then locked hint / approach / solution chests; peek if you must, but forfeit the unaided bonus.
- **Boss battles** — timed mock-interview rounds against boss toys. Beat the clock before the Jack-in-the-Box springs.
- **Merit badges & streaks** — sticker badges, a wind-up charge meter, and a spinning-top streak to keep progress tangible.

## Tech stack

- [Next.js](https://nextjs.org) 16 (App Router)
- React 19
- TypeScript 5
- Fonts: Fredoka + Nunito via `next/font`

## Project structure

```
frontend/
  app/               # Next.js App Router
    page.tsx         # Landing + auth flow (with confetti)
    academy/         # Academy dashboard (quests, boss, achievements, …)
    layout.tsx       # Root layout, fonts, metadata
    globals.css
  components/         # Landing, Auth, Confetti, PushButton, academy/*
```

## Getting started

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the landing page; the Academy dashboard lives at `/academy`.

## Scripts

Run from the `frontend/` directory:

| Command         | Description                |
| --------------- | -------------------------- |
| `npm run dev`   | Start the dev server       |
| `npm run build` | Production build           |
| `npm run start` | Serve the production build |
| `npm run lint`  | Run ESLint                 |
