# Project: caraquista-reflex

## Architecture
- **Framework**: Reflex (Next.js frontend + FastAPI backend + WebSockets + Radix UI + Tailwind CSS)
- **Theme**: Dark Navy (`#070B19`), Glassmorphism Cards (`#0D152B`), Gold Accents (`#FDB827`), Inter/Geist typography.
- **Data & APIs**: Supabase PostgreSQL (`games`, `teams`, `batting_stats`, `pitching_stats`, `players`, `elo_ratings`) + MLB Stats API (`sportId=17`, `leagueId=135`, live feed, team stats, fielding).
- **Core Sabermetrics (`core/`)**:
  - `supabase_client.py`: Ingestion, weighted aggregation, day/night records, ISO weeks records, fielding stats, collective stats.
  - `elo.py`: ELO ratings base 400 with home field advantage (+35 pts) & 5,000 Monte Carlo iterations.
  - `wpa_engine.py`: Tango RE24 24-state matrix with `BASE_STATE_MAP`, Win Expectancy, Leverage Index (LI), Clutch.
  - `situational.py`: Splits (RISP, Clutch, Bases Loaded, BvP) & LOB Tracker (3rd out & in-inning RISP LOB).
  - `bullpen_lineups.py`: Inherited runners (IR/IRS/IRS%) & 1-9 batting order tracking / heatmaps.
  - `spray_chart.py`: BIS deterministic hardness classification (Hard/Medium/Soft) on geometric diamond.
  - `strike_zone.py`: 3x3 plate discipline matrix (O-Swing%, Z-Contact%, CSW%, Whiff%).
  - `cache.py`: In-memory TTL cache decorator.
- **Application Pages (`republicaraquistapp/pages/`)**:
  1. `/` (`index.py`): Executive dashboard, scoreboard, KPIs, Day/Night, ISO Weeks.
  2. `/standings` (`standings.py`): Official standings, Pythagorean expectation, ELO Power Rankings, 5k Monte Carlo simulation, Day/Night, ISO Weeks.
  3. `/individuales` (`individuales.py`): Batting, Pitching, Fielding/Defense (PO, A, E, TC, FPCT, DP, RF/9, CS, SB, CS%, PB), H2H comparator.
  4. `/colectivas` (`colectivas.py`): 8 LVBP teams collective Batting, Pitching, Fielding with Plotly horizontal charts.
  5. `/wpa` (`wpa.py`): Game-by-game Win Expectancy curves, Leverage Index, heroes/villains, season leaders.
  6. `/situacional` (`situacional.py`): Splits (RISP, Clutch, Bases Loaded), LOB Tracker (3rd out & in-inning), BvP matrix.
  7. `/spray-charts` (`spray_charts.py`): Interactive spatial spray charts with BIS hardness, Strike Zone heatmaps.
  8. `/bullpen` (`bullpen.py`): Reliever inherited runners (IR/IRS/IRS%), 1-9 batting order tracking & heatmaps.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | WPA 24-States Engine | Tango RE24 24-state matrix with `BASE_STATE_MAP` alignment | M1 | survey |
| 2 | LOB Tracker Engine | `compute_lob_analytics` for 3rd out and in-inning RISP LOB | M1 | survey |
| 3 | BIS Spray Chart Engine | Port `spray_chart.py` with deterministic hardness and diamond coords | M1 | survey |
| 4 | Strike Zone Engine | Port `strike_zone.py` with 3x3 discipline metrics (CSW%, Whiff%) | M1 | survey |
| 5 | Supabase Client Sync | Add `get_weekly_records`, `get_collective_team_stats`, `get_individual_fielding_stats`, fix OBP | M1 | survey |
| 6 | Navigation & Layout | 8-route Navbar, Dark Navy/Glassmorphism theme, responsive drawer | M2 | survey |
| 7 | Reactive State Hub | Centralized `AppState` and sub-states with TTL caching | M2 | survey |
| 8 | Dashboard Home (`/`) | Scoreboard, KPIs, Day/Night record, ISO weeks record | M3 | survey |
| 9 | Standings & ELO (`/standings`) | Standings, Pythagorean $xW$, ELO 5k Monte Carlo, ISO weeks | M3 | survey |
| 10 | Individual & Fielding Stats (`/individuales`) | Batting, Pitching, Fielding/Defense, H2H comparator | M4 | survey |
| 11 | Collective Stats 8 Teams (`/colectivas`) | 8 LVBP teams in Batting, Pitching, Fielding with Plotly | M4 | survey |
| 12 | WPA & Win Expectancy (`/wpa`) | Interactive Win Expectancy curves, Leverage Index, Clutch | M5 | survey |
| 13 | Situational & LOB (`/situacional`) | Splits (RISP, Clutch), LOB Tracker, BvP matrix | M5 | survey |
| 14 | Spray Charts & Strike Zone (`/spray-charts`) | BIS Diamond Spray Charts & 3x3 Plate Discipline Heatmaps | M5 | survey |
| 15 | Bullpen & Lineups (`/bullpen`) | Relievers IR/IRS/IRS% & 1-9 batting order tracking/heatmaps | M5 | survey |
| 16 | E2E Test Suite | Opaque-box parity tests against RepubliCaraquistApp (Tiers 1-4) | E2E_Track | survey |
| 17 | Adversarial Hardening & Audit | Tier 5 adversarial tests, edge cases, forensic integrity verification | Final_Milestone | survey |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Core Engines & Math Parity | `core/` modules sync (`wpa_engine`, `situational`, `spray_chart`, `strike_zone`, `supabase_client`) | none | IN_PROGRESS |
| M2 | Navigation & State Architecture | `navbar.py`, `layout.py`, `app_state.py`, theme & styling | none | IN_PROGRESS |
| M3 | Dashboard & Standings | `/` (`index.py`) & `/standings` (`standings.py`) with Day/Night, ISO Weeks, ELO, Monte Carlo 5k | M1, M2 | PLANNED |
| M4 | Individual, Defense & Collective | `/individuales` & `/colectivas` with Batting, Pitching, Fielding, 8 teams, Plotly charts | M1, M2 | PLANNED |
| M5 | Advanced Sabermetrics Suite | `/wpa`, `/situacional`, `/spray-charts`, `/bullpen` | M1, M2 | PLANNED |
| E2E | E2E Testing Track | Independent test suite validating parity with RepubliCaraquistApp | none | IN_PROGRESS |
| M_Final | Final Verification & Hardening | Pass 100% E2E tests, Adversarial Hardening (Tier 5), Forensic Audit | M3, M4, M5, E2E | PLANNED |

## Interface Contracts
### `core/wpa_engine`
- `encode_base_state(on_1b: bool, on_2b: bool, on_3b: bool) -> int`: Maps 8 runner combinations to keys 0..7 (explicitly: `(False, False, True) -> 3`, `(True, True, False) -> 4`).
- `get_leverage_index(inning: int, half: str, outs: int, base_state: int, score_diff: int) -> float`
- `calculate_wpa_for_game(game_pk: int) -> dict`

### `core/situational`
- `compute_lob_analytics(df_plays: pd.DataFrame) -> dict`: Returns `lob_by_team`, `lob_by_player`, `inning_risp_lob_by_team`, `inning_risp_lob_by_player`.

### `core/supabase_client`
- `get_weekly_records(season: int) -> pd.DataFrame`: Returns DataFrame with columns `['semana', 'w', 'l', 'pct', 'cf', 'cp', 'dif']`.
- `get_collective_team_stats(season: int) -> dict`: Returns `{'batting': df_bat, 'pitching': df_pitch, 'fielding': df_field}` for all 8 LVBP teams.
- `get_individual_fielding_stats(season: int) -> dict`: Returns `{'fielders': df_fielders, 'catchers': df_catchers}`.
- Standard OBP: `(H + BB + HBP) / (AB + BB + HBP + SF)`.

### `core/spray_chart` & `core/strike_zone`
- `generate_spray_chart_figure(df_plays: pd.DataFrame, player_name: str) -> go.Figure`
- `generate_strike_zone_figure(df_pitches: pd.DataFrame, player_name: str) -> go.Figure`

## Code Layout
```
caraquista-reflex/
├── assets/                          # Static assets (logo.png, team logos, favicon)
├── core/                            # Analytical engines & data layer
│   ├── cache.py
│   ├── teams.py
│   ├── supabase_client.py
│   ├── elo.py
│   ├── wpa_engine.py
│   ├── situational.py
│   ├── bullpen_lineups.py
│   ├── spray_chart.py
│   └── strike_zone.py
├── republicaraquistapp/
│   ├── republicaraquistapp.py       # Main Reflex App entry point & routing registration
│   ├── components/                  # Shared UI components
│   │   ├── navbar.py                # 8-route responsive navbar
│   │   ├── layout.py                # App frame, background, glassmorphism container
│   │   ├── scoreboard.py            # Scoreboard widget
│   │   └── cards.py                 # Stat cards & KPI components
│   ├── pages/                       # The 8 SPA views
│   │   ├── index.py                 # / (Home / Dashboard)
│   │   ├── standings.py             # /standings
│   │   ├── individuales.py          # /individuales
│   │   ├── colectivas.py            # /colectivas
│   │   ├── wpa.py                   # /wpa
│   │   ├── situacional.py           # /situacional
│   │   ├── spray_charts.py          # /spray-charts
│   │   └── bullpen.py               # /bullpen
│   ├── state/                       # Reflex Reactive States
│   │   ├── base_state.py            # AppState base & common filters
│   │   ├── standings_state.py
│   │   ├── stats_state.py
│   │   ├── wpa_state.py
│   │   ├── situational_state.py
│   │   ├── spray_state.py
│   │   └── bullpen_state.py
│   └── styles/
│       └── theme.py                 # Official palette and CSS styles
├── tests/                           # E2E & Sabermetric parity test suite
│   ├── test_sabermetrics.py
│   ├── test_analytical_parity.py
│   └── test_reflex_routes.py
├── rxconfig.py                      # Reflex configuration
└── requirements.txt
```
