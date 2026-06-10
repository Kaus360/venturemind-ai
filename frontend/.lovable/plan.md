# VentureMind AI — Build Plan

A premium dark, animated single-page app over TanStack Router, talking to your FastAPI backend via a configurable base URL. No mock data — every screen calls the real endpoints you listed.

## Routing (TanStack Router, file-based)

```
src/routes/
  __root.tsx              # Sidebar + Topbar shell, providers, Toaster
  index.tsx               # Dashboard
  autopilot.tsx           # Autopilot
  startups.tsx            # Startup Explorer
  market-gaps.tsx         # Market Gap Finder
  admin.tsx               # Admin Control Room
  report.tsx              # Consolidated Report
  wizard.tsx              # Layout: progress bar + <Outlet/>
  wizard.step-1.tsx … wizard.step-7.tsx
```

## Backend configuration

- `VITE_API_BASE_URL` env var, default `http://localhost:8000`.
- In-app override: Admin screen has an "API Base URL" field persisted to `localStorage` (`vm.apiBaseUrl`); a small `apiClient` reads from localStorage → env → default.
- Centralized `src/lib/api.ts` with typed wrappers for every endpoint, all using try/catch and surfacing errors via sonner toasts.
- A tiny status pill in the topbar shows the active base URL and reachability.

Endpoints wired exactly as specified: `/api/v1/generate-problems`, `/generate-solution`, `/validate-startup`, `/analyze-competitors`, `/redteam-critique`, `/generate-roadmap`, `/execute-workflow`, `/memory-context`, plus the `/ml/...` scoring, retrieval, embeddings, and infrastructure routes.

## State

`src/context/VentureContext.tsx` — single provider mounted in `__root.tsx`, holding: `domain, problems, selectedProblem, problemStatement, customFocus, audienceOverride, solution, startupIdea, validation, competitorData, criticFeedback, roadmap`, plus `loadFromMemory(record)` and `reset()`. Persisted to `sessionStorage` so refresh on `/report` works.

## Shell

- **Sidebar:** gradient wordmark, nav items with animated left-accent slide-in, active state via `useRouterState`. Memory History section calls `GET /memory-context` on mount + after each wizard completion, lists last 5 with verdict pill.
- **Topbar:** breadcrumb from current route, health dot polling `/ml/infrastructure/health` every 30s (radial pulse when healthy, blink when degraded), "New Venture Scan" → `/autopilot`.

## Screens

1. **Dashboard (`/`)** — hero with sequential word fade-in, SVG drifting neural curves + floating particles in background, two CTAs, stats row (from memory + health), staggered history grid → "Open Report" loads into context and routes to `/report`. Skeletons + error+retry banner.
2. **Wizard layout** — sticky progress bar (15/30/45/55/75/88/95/100%), Framer Motion `AnimatePresence` slide (x ±40, fade) between steps keyed by pathname.
   - **Step 1** preset pills + input → `POST /generate-problems` → 3 cards with impact/feasibility gauges (Recharts radial), cascade spring entrance, glowing border trace on hover.
   - **Step 2** editable summary, focus textarea, audience override (client-only).
   - **Step 3** on-mount `POST /generate-solution`; split editor + features list with add/remove.
   - **Step 4** `POST /validate-startup` then `POST /ml/scores/startups`; central composite gauge with count-up grade, 4 metric cards with glow-orb backdrops, weaknesses, recommendations.
   - **Step 5** `POST /analyze-competitors` then `POST /ml/competitors/analyze`; competitor table, semantic matches, gaps, recommendations.
   - **Step 6** `POST /redteam-critique`; verdict card scale-in + pulsing glow color-matched to PASS/NEEDS_WORK/FAIL, two flaw columns, viability bar.
   - **Step 7** `POST /generate-roadmap`; MVP list, 3 phase panels, scaling strategy, "View Final Venture Report".
3. **Report (`/report`)** — export bar (PDF via `window.print`, JSON via Blob download, "Index in Database" → `POST /ml/embeddings/startups`), tab nav with crossfade, radar chart on Metrics tab with sequential axis draw.
4. **Autopilot (`/autopilot`)** — domain input → `POST /execute-workflow`. Custom LangGraph visualizer: SVG nodes + animated edges using `stroke-dashoffset`, sequential activation timeline tied to backend response (or staged simulation if response is single-shot), spinning arc on active node, checkmark on done, X+rose on fail. Live console with typewriter log lines + timestamps. On completion → "Open Consolidated Report".
5. **Startup Explorer (`/startups`)** — search + domain filter + top_k slider → `POST /ml/retrieval/startups`. Result cards with similarity pill, delete confirm modal, "Add Startup" modal → `POST /ml/embeddings/startups`.
6. **Market Gaps (`/market-gaps`)** — `POST /ml/retrieval/market-gaps` grid + `POST /ml/retrieval/competitors` rendered as an animated SVG sonar radar (sweeping arc, plotted dots by similarity).
7. **Admin (`/admin`)** — health panels (Postgres, Qdrant), API base URL editor, "Bootstrap Collections" → `POST /ml/infrastructure/bootstrap`, "Graceful Shutdown" with double-confirm modal → `POST /ml/infrastructure/shutdown?confirm=true`.

## Design system

- Inter via `<link>` in `__root.tsx` head (no remote `@import` in CSS).
- `src/styles.css` `@theme` tokens for the full palette (indigo/violet/emerald/amber/rose), glass surface mix, plus `@keyframes` for `gradient-shift`, `pulse-glow`, `shimmer`, `dash-flow`, `float-up`, and `@utility glass`, `glass-inner-top`, `text-gradient-brand`.
- Semantic tokens only in components (`bg-background`, `text-primary`, etc.) — no raw `bg-slate-950` sprinkled in JSX; the slate palette is recreated as HSL/oklch tokens to keep the rule "no custom color classes in components" and still hit your exact hues.
- Animated gradient mesh background mounted at the shell level.
- Framer Motion for page/step transitions, staggered grids, scale entrances; Recharts animation props for gauges/radar.

## Reusable components

`GlassCard`, `GradientText`, `HealthDot`, `ScoreGauge`, `VerdictBadge`, `ProgressRail`, `ParticleField`, `NeuralBackground`, `LangGraphVisualizer`, `TypewriterLog`, `CountUp`, `ConfirmModal`, `SectionHeader`, `EmptyState`, `ErrorBanner`, `Skeletons`.

## Dependencies to add

`framer-motion`, `recharts`. (Lucide, sonner, TanStack Router/Query already present.)

## Out of scope / caveats

- The preview cannot reach `http://localhost:8000`; until you point `VITE_API_BASE_URL` at a tunneled/deployed backend (or set it in Admin), every screen will show its real error state — by design, no mocks.
- Spec says "React Router"; built with TanStack Router per your confirmation. URLs and behavior match.
- The LangGraph step timing animates client-side over the single `/execute-workflow` response (the endpoint doesn't stream per-node events).
