# New Frontend — Implementation Plan

Status: **planning only — no code written yet.**

## 0. Constraints (non-negotiable)

- The existing Streamlit dashboard (`app.py`, `api_client.py`) is **not touched,
  modified, or removed**. It keeps running exactly as-is via
  `streamlit run app.py`.
- `api.py`, `scraper.py`, `geocode.py` are **not modified** for this work.
  Per the answered clarifying question, the new frontend reads:
  - **Live data** (institutions, regions, countries, states, geocoded
    lat/lon, cache/meta status) **only from the existing `api.py` HTTP
    endpoints** — no new backend endpoints are added.
  - **Static data** (AFU principles table, Best Practices CSV, population-65+
    figures, `india_outline.geojson`) is served **directly as static files**
    bundled with the new frontend, copied from the existing repo CSVs/geojson
    (see §5). Nothing in the repo root is deleted or renamed — copies only.
- All new code lives in a new top-level `frontend/` directory. Nothing
  outside it is created or altered by this work, other than this plan file
  and (optionally, at the end) a short new section in `CLAUDE.md` describing
  the new frontend once it exists.

## 1. Tech stack

- **React 18 + TypeScript + Vite** — fast dev server, instant HMR, simple
  static build (`vite build` → `frontend/dist`, deployable as plain static
  files, no Node server required in production).
- **Tailwind CSS** for styling, with a custom design-token theme (§3) driving
  both light and dark mode via Tailwind's `dark:` class strategy.
- **React Router** for the 5-page navigation (client-side, matches the
  Streamlit sidebar's page switcher).
- **Charts**: `Plotly.js` via `react-plotly.js` for the geographic maps
  (choropleth + scattergeo, matching the existing India-outline-overlay
  technique) and `Recharts` for the simpler bar/donut/stacked-bar charts —
  Recharts is lighter weight and more idiomatic in React for those, Plotly is
  kept only where geo projection is actually needed.
- **State/data fetching**: `@tanstack/react-query` for the live API calls
  (caching, retry, background refetch — mirrors `st.cache_data`'s role in the
  Streamlit app) plus a small `fetch`-based client (`src/lib/apiClient.ts`,
  the React analogue of `api_client.py`).
- **Icons**: `lucide-react` (clean, consistent, accessible line icons).
- **Fonts**: self-hosted **Atkinson Hyperlegible** for body/UI text (designed
  by the Braille Institute specifically for readability/low vision — a strong
  fit for "age-friendly") and **Lexend** as a fallback/heading option (also
  designed for reading proficiency). Both loaded as local `@font-face` files
  (no external font CDN calls, so the app works offline and loads fast).

## 2. Directory structure

```
frontend/
  index.html
  package.json
  vite.config.ts
  tailwind.config.ts
  tsconfig.json
  public/
    data/                      # static snapshots, see §5
      principles.json
      best_practices.json
      population_65.json
      india_outline.geojson
    fonts/
      AtkinsonHyperlegible-*.woff2
      Lexend-*.woff2
  src/
    main.tsx
    App.tsx                    # router + theme provider shell
    theme/
      ThemeProvider.tsx         # light/dark context, persisted to localStorage
      tokens.css                 # CSS custom properties (§3)
    lib/
      apiClient.ts               # typed fetch wrapper around api.py endpoints
      staticData.ts              # loaders for public/data/*.json + geojson
      countryNameMap.ts          # port of API_TO_STATIC_COUNTRY_NAME
    hooks/
      useMeta.ts, useRegions.ts, useCountries.ts, useMembers.ts  # react-query hooks
    components/
      layout/
        AppShell.tsx             # sidebar/topbar nav, responsive collapse
        ThemeToggle.tsx
        LiveStatusBadge.tsx      # green/red API-connected pill, refresh button
      cards/
        KpiCard.tsx
        StatCard.tsx
        InstitutionCard.tsx
        BestPracticeCard.tsx     # expandable card, replaces st.expander
      charts/
        RegionDonutChart.tsx
        RegionBarChart.tsx
        PrincipleBarChart.tsx
        AudienceBarChart.tsx
        CoverageStackedBarChart.tsx
        DensityBarChart.tsx
      maps/
        WorldImpactMap.tsx       # Plotly choropleth+scattergeo, India overlay
        RegionFilterTabs.tsx
    pages/
      GlobalOverviewPage.tsx
      PrincipleGapAnalysisPage.tsx
      RegionalEquityPage.tsx
      BestPracticesExplorerPage.tsx
      ImpactMapPage.tsx
    types/
      institution.ts, principle.ts, bestPractice.ts, ...
  scripts/
    sync-static-data.mjs        # dev-time helper, see §5
```

## 3. Visual design system — "Claude-themed pastel terracotta"

### 3.1 Palette (defined as CSS custom properties, light values on `:root`,
dark values under `.dark`)

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#FAF6F1` (warm cream) | `#211D1A` (espresso charcoal) | page background |
| `--surface` | `#FFFFFF` | `#2B2521` | cards, panels |
| `--surface-muted` | `#F3EAE1` | `#332C27` | secondary panels, table stripes |
| `--border` | `#E8DCCE` | `#40372F` | card/divider borders |
| `--text-primary` | `#2A2119` | `#F3EAE1` | body text |
| `--text-secondary` | `#6B5D4F` | `#B8A996` | captions, labels |
| `--terracotta` | `#D97757` | `#E38A68` | primary brand/accent (Claude's signature warm terracotta) |
| `--terracotta-soft` | `#F3D9CB` | `#4A3226` | pastel fill (chart bars, active-tab bg) |
| `--clay` | `#C97B63` | `#D98F76` | secondary accent |
| `--sage` | `#8FA888` | `#7E9C77` | success / "well implemented" |
| `--amber` | `#E0A458` | `#E3B06B` | warning / "moderate" |
| `--rose` | `#C96A6A` | `#D97F7F` | alert / "underimplemented" / gap |
| `--ocean` | `#6E97A8` | `#7FA9BA` | info accent, secondary region color |

Region colors keep the *hue identities* from the current dashboard
(red≈NA, blue≈Europe, orange≈Asia, purple≈Oceania, teal≈S.America) but are
re-mixed into the same pastel-terracotta family so nothing clashes:
`--region-na: #D97757`, `--region-europe: #6E8FA8`, `--region-asia: #E0A458`,
`--region-oceania: #A487A0`, `--region-samerica: #6EA89A`. Same hex pairs
defined for dark mode with slightly raised lightness for contrast on dark
surfaces.

### 3.2 Typography

- Base font size **18px** (vs. the web default 16px) — larger baseline for
  readability, per "age-friendly" requirement.
- Font stack: `"Atkinson Hyperlegible", "Lexend", system-ui, sans-serif`.
- Line height **1.6** for body copy, **1.3** for headings.
- Minimum body text size never below **16px** anywhere (no fine-print
  captions smaller than that, unlike the current dashboard's 0.65rem labels).
- Headings use a restrained scale (1.25 ratio) so pages don't feel
  cluttered: `text-sm/base/lg/xl/2xl/3xl` Tailwind scale mapped to the above.
- Numerals in KPI tiles use `font-variant-numeric: tabular-nums` for clean
  alignment.

### 3.3 Shape & elevation

- Rounded corners: `rounded-xl` (12px) on cards, `rounded-full` on
  pills/tabs/badges — soft, approachable, matches Claude's UI language.
- Shadows: soft, low-contrast (`shadow-sm`/`shadow-md` only, no harsh drop
  shadows), consistent between light/dark (dark mode uses a subtle lighter
  border instead of shadow, since shadows read poorly on dark backgrounds).
- Generous whitespace: minimum 16px card padding, 24px section gaps —
  avoids the current dashboard's very dense, small-font "trading terminal"
  layout, in favor of a calmer, easier-to-scan one.

### 3.4 Light/dark mode

- `ThemeProvider` stores `"light" | "dark" | "system"` in `localStorage`,
  defaults to `system` (reads `prefers-color-scheme`), toggle lives in the
  top bar (sun/moon icon button, `lucide-react`).
- All charts (Plotly + Recharts) read the active theme's tokens for
  background/gridline/text colors so charts restyle instantly on toggle
  (no separate hardcoded dark-only chart theme like the current
  Streamlit app's Impact Map page).

### 3.5 Accessibility & "simple to interact" requirements

- All interactive elements (buttons, tabs, map region pins) have a minimum
  **44×44px** touch target and visible focus rings (`focus-visible:ring-2`).
- Color is never the only signal — gap-analysis status (Well/Moderate/Under
  implemented) pairs color with an icon + text label.
- Charts include a text/table fallback (e.g. a `<details>` "View as table"
  under each chart) so the data is available to screen readers and anyone
  who finds visual charts hard to parse.
- Map markers and chart bars have descriptive `aria-label`s; the site is
  navigable by keyboard alone (tab through nav → filters → chart legends →
  cards).
- Contrast: every text/background pairing in §3.1 is checked against WCAG AA
  (4.5:1 body text, 3:1 large text) in both modes before implementation.

## 4. Responsive / mobile-friendly layout

- Mobile-first Tailwind breakpoints. Sidebar nav (desktop) collapses into a
  bottom tab bar or hamburger drawer on screens `< 768px` — five destinations
  map to five icons, consistent with a native-app feel that's easy for less
  tech-savvy users to tap.
- The two/three-column layouts on Global Overview and Impact Map
  (map + charts, or countries/map/institutions) stack vertically on mobile:
  map first (full width), then charts/lists below, in priority order.
- KPI tile rows scroll horizontally on narrow screens (snap-scroll) instead
  of shrinking to illegible text, OR wrap to a 2-column grid — decide during
  implementation based on how many tiles are shown per page (2-col grid is
  the current default plan).
- Maps: touch-friendly pinch-zoom/pan (Plotly's default touch handling),
  larger marker hit-areas on touch devices, and a "tap card instead of
  hover" interaction pattern for institution tooltips on mobile (hover
  tooltips don't work well on touch).
- All pages tested at 375px (small phone), 768px (tablet), 1440px (desktop).

## 5. Data layer

### 5.1 Live (fetched from the running `api.py`, unmodified)

`src/lib/apiClient.ts` wraps these existing endpoints (base URL configurable
via `VITE_API_BASE_URL`, default `http://127.0.0.1:8000`, mirroring
`AFU_API_BASE_URL` in `api_client.py`):

- `GET /meta` — cache status / live-connection badge
- `GET /members`, `GET /members?region=`, `GET /members?country=` —
  institution lists (name, url, lat/lon)
- `GET /members/regions` — per-region institution counts
- `GET /members/countries`, `GET /members/countries?region=` — per-country
  counts
- `POST /refresh` — manual refresh button, same as the Streamlit sidebar

React Query hooks cache these client-side (`staleTime` tuned similarly to
the API's 12h server-side TTL) and expose `{data, isLoading, isError}` to
pages/components. If the API is unreachable, hooks report an error and
components fall back to the static country list bundled in
`public/data/` (a straight port of `STATIC_INSTITUTIONS` /
`load_static_country_data()`), exactly mirroring the existing
API-down-fallback behavior in `app.py` — just without ever calling into
`api.py`'s Python code.

### 5.2 Static (served directly as files, not through any API)

These files are **copies**, generated once (and re-run manually whenever the
source CSVs change) by `frontend/scripts/sync-static-data.mjs`, a small
Node script that reads the existing repo-root CSVs/geojson and writes JSON
into `frontend/public/data/`. It never modifies the source files.

| Static file | Source in repo root | Used for |
|---|---|---|
| `public/data/principles.json` | the 10-row principles table currently hardcoded in `app.py`'s `load_principles_data()` | Principle Gap Analysis page bar chart + KPI tiles |
| `public/data/best_practices.json` | `Form_Data_Entry-Grid_view.csv` | Best Practices Explorer page cards/filters |
| `public/data/population_65.json` | `populatio_65+_worldbank.csv` | Regional Equity page density chart |
| `public/data/india_outline.geojson` | `india_outline.geojson` | India boundary overlay on every map, **per the CLAUDE.md rule that this must reflect the Indian Constitution/Government of India boundary** — copied verbatim, never redrawn |
| `public/data/static_country_snapshot.json` | `load_static_country_data()` / `STATIC_INSTITUTIONS` in `app.py` | API-down fallback for country markers/lists |

This keeps a single script as the one place that "syncs" static data, run
manually during development/deploy — no runtime dependency on Python or the
CSVs being present in production, and the CSVs remain the single source of
truth (script is a copy step, not a fork).

## 6. Pages & content inventory

Every page below is a 1:1 feature-parity target against the current
Streamlit page of the same purpose — same information, redesigned
presentation. Nothing from the existing dashboard is dropped.

### 6.1 Global Overview (`/`)
- KPI card row: Member Institutions, N. America Share %, Countries,
  Best Practices count, P5/P7 citation rate, Submission rate.
- `WorldImpactMap`: world choropleth/scatter map with the India-outline
  overlay, region pin clustering, sized by institution count, region filter
  pill-tabs (Global/NA/Europe/Asia/S.America/Oceania) below the map.
- Side panel: `RegionDonutChart` (share of institutions by region, click a
  slice to filter the map) + `RegionBarChart` (institutions per region,
  click a bar to filter the map) — same cross-filtering interaction as
  today's `plotly_events`/`on_select`, implemented via shared React state
  instead.

### 6.2 Principle Gap Analysis (`/principles`)
- KPI cards: Well/Moderately/Under-implemented counts, "most critical gap"
  callout (P5 & P7).
- `PrincipleBarChart`: horizontal bar, citation % per principle, colored by
  Well/Moderate/Under, 50% reference line, "View as table" fallback.
- Callout banner for the P5/P7 gap.
- `AudienceBarChart`: activities-by-target-audience horizontal bar, derived
  from `best_practices.json`.

### 6.3 Regional Equity (`/regional-equity`)
- `CoverageStackedBarChart`: countries in-network vs. not, per region +
  a compact coverage table beside/below it.
- `DensityBarChart`: AFU institutions per million seniors per country
  (population_65.json), colored by region.
- Insight callout card (Ireland high / China underserved, etc., computed
  from the data rather than hardcoded where possible).

### 6.4 Best Practices Explorer (`/best-practices`)
- Filter bar: multi-select Principle filter, multi-select University filter
  (both searchable comboboxes, mobile-friendly full-screen filter sheet on
  small screens instead of dropdowns).
- KPI row: Ongoing / One-Time / Unique Universities counts for the filtered
  set.
- Filtered `PrincipleBarChart` mini-variant.
- `BestPracticeCard` list: one expandable card per submission (title,
  university, purpose, outcomes, uniqueness, principles, type, duration) —
  replaces `st.expander` rows.

### 6.5 Impact Map (`/impact-map`)
- Region tab row above the map (five regions, tap to drill in).
- `WorldImpactMap` in "impact" mode: region → country → institution
  drill-down, India overlay, ISO-based region highlight tint.
- Responsive 3-pane layout (countries list / map / institutions list) that
  collapses to stacked panels on mobile, with the currently-selected
  level's list shown as a bottom sheet/accordion instead of a side column.
- Stat tiles under the map reflecting current drill-down level (global /
  region / country), same numbers as today.

### 6.6 Shared shell
- Top bar: app title/logo, live-API status badge (green "Connected — N
  institutions, updated Xm ago" / red "Live API unavailable — static
  snapshot"), manual refresh button, theme toggle.
- Sidebar/bottom-nav: the five pages above.
- Footer: data source attribution (AFU-API live service, AFU Best Practices
  Database, World Bank SP.POP.65UP.TO, UN WPP 2025) + paper citation, ported
  verbatim from the current sidebar text.

## 7. Interaction parity notes (things easy to regress if skipped)

- Cross-filtering: clicking a donut slice or bar in Global Overview updates
  the map filter — implement as lifted React state (`selectedRegion`) passed
  into both chart and map components, not global/global mutation.
- Drill-down state in Impact Map (`selectedRegion`, `selectedCountry`) is
  URL-synced (`/impact-map?region=Asia&country=India`) so links are
  shareable/bookmarkable — an improvement over the current
  `st.session_state`-only approach, but must preserve the same toggle-off
  behavior (clicking the active region again clears the selection).
- Institution markers without geocoded coordinates still need a visible
  fallback position (deterministic jitter around the country centroid,
  ported from `institution_points()`), so no country silently loses its
  marker count.

## 8. Build/run

- `frontend/package.json` scripts: `dev` (Vite dev server, default port
  `5173`, proxies `/api/*` to `VITE_API_BASE_URL` in dev to dodge CORS even
  though `api.py` already sets `allow_origins=["*"]`), `build`, `preview`.
- Runs **alongside**, not instead of, the existing stack:
  - `uvicorn api:app --reload --port 8000` (unchanged)
  - `streamlit run app.py` (unchanged, still works, still the "current"
    dashboard)
  - `cd frontend && npm run dev` (new, separate port, e.g. `5173`)
- A short new "New frontend (`frontend/`)" section will be added to
  `CLAUDE.md` once the app exists, documenting these run commands next to
  the existing Streamlit ones — not replacing them.

## 9. Suggested build order (phases)

1. Scaffold Vite+React+TS+Tailwind app, theme tokens, `ThemeProvider`,
   font loading, `AppShell` with nav + theme toggle (empty pages).
2. `apiClient.ts` + React Query hooks + `LiveStatusBadge`, wire up
   `/meta`, `/members/regions`, `/members/countries` against the running
   API.
3. `sync-static-data.mjs` + static JSON files + `staticData.ts` loaders.
4. Global Overview page (map + donut + bar + cross-filtering) — the most
   complex page, validates the map/chart/theme plumbing for every later page.
5. Principle Gap Analysis + Regional Equity pages (simpler, chart-only).
6. Best Practices Explorer (filters + cards).
7. Impact Map page (drill-down + URL sync).
8. Responsive pass on all pages at 375/768/1440px; keyboard-nav and
   contrast audit against §3.5.
9. Cross-browser/light-dark visual QA, then hand off for review.

## 10. Explicit non-goals

- No changes to `app.py`, `api.py`, `api_client.py`, `scraper.py`,
  `geocode.py`, or any CSV/JSON data file in the repo root.
- No new backend endpoints.
- No removal of the Streamlit dashboard — both frontends coexist
  indefinitely unless the user later decides otherwise.
