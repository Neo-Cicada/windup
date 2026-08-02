# Windup Academy — Frontend

Next.js 16 (App Router) + React 19 client for the Windup Academy API. Every screen
renders server data fetched through `lib/api.ts`, so the backend and a judge worker
have to be running for the app to do anything — see the [root README](../README.md).

## Getting started

```bash
npm install                  # postinstall copies the Pyodide runtime into public/pyodide/
cp .env.example .env.local   # NEXT_PUBLIC_API_URL, if the API isn't on :8000
npm run dev
```

Landing page at [http://localhost:3000](http://localhost:3000); the academy dashboard
is at `/academy` and needs a session (demo toy: `bramble@playroom.com` / `windup123`).

| Command            | Description                              |
| ------------------ | ---------------------------------------- |
| `npm run dev`      | Dev server on :3000                      |
| `npm run build`    | Production build                         |
| `npm run start`    | Serve the production build               |
| `npm run lint`     | ESLint — React Compiler rules are errors |
| `npx tsc --noEmit` | Typecheck without building               |

There is no frontend test runner.

## Layout

- `app/` — one folder per route; each `page.tsx` is a server shell that exports
  `metadata` and renders one client container.
- `components/academy/routes/` — the containers, which own state and fetching.
  `components/academy/screens/` stays presentational: props and callbacks only.
- `lib/api.ts` — the only place that talks to the API. Holds the tokens, attaches the
  bearer header, and refreshes once on a 401.
- `lib/runners/` — the browser engines behind the **Run** button (Pyodide for Python
  and SQL, a plain Worker for JavaScript). Run grades nothing; **Submit** goes to the
  judge, which does.
- Styling is inline style objects. `app/globals.css` holds the resets, the keyframes,
  and the responsive overrides — an inline style can't carry a media query, so every
  breakpoint is a class in there.

`AGENTS.md` (aliased by `CLAUDE.md`) is the note that this Next.js version has
breaking changes versus older ones; the bundled guides in
`node_modules/next/dist/docs/` are the reference.
