# Changelog

All notable changes to this project. Versions follow [semver](https://semver.org); dates are ISO.

## 2.0.0 — 2026-11-27

Interface, structure and documentation overhaul. **No pricing, calibration or simulation logic was changed** — all
headline numbers are identical to 1.x because they still come from the same `utils/pipeline.py` and
`results/gwp1_results.json`.

### Added
- `utils/theme.py` — design system: design tokens published as CSS custom properties, global stylesheet, HTML
  components (page header, KPI tiles, panels, badges, callouts, empty states) and the Plotly template. One palette
  for the whole app.
- `utils/fmt.py` — shared number formatting (`money`, `pct`, `bp`, `delta_span`, `describe_change`) so units and
  decimals cannot drift between pages.
- `USER_GUIDE.md` — task-by-task usage guide: setup, orientation, nine common workflows, a glossary of what each
  metric does *not* mean, troubleshooting and a "where to change things" map.
- `CHANGELOG.md`, `.env.example`.
- Grouped navigation in `app.py` (`st.navigation` with five labelled sections) and deep-link url paths.
- Every page: loading, empty and error states. `utils.ui.guard()` contains a failure inside one section instead of
  blanking the page.
- Pricing Workbench: CSV template download, explicit validation messages, Feller badge, Greeks table with a units
  note, CSV + Excel export of the exact on-screen numbers.
- Model Diagnostics: residual heatmap with a call/put correlation read-out, parameter-sensitivity ranking,
  quadrature settings, IV surface, regime comparison.
- Report page: results workbook with one sheet per step; inline PDF/HTML viewers with their own download buttons.
- About & Docs: merged documentation index with inline reader, security tab, contact form with validation,
  disclaimer tab.
- Tests: page smoke test now covers the new navigation and all twelve pages.

### Changed
- `pages/0_Home.py` — dashboard rebuilt around five KPI tiles, a market/model split, and deliverable cards.
- `pages/1_Live_Simulation.py` → **Pricing Workbench** — three numbered blocks (parameters, contract, export)
  instead of a wall of seven-column rows.
- `pages/3_AI_Explainability.py` → **Model Diagnostics** — renamed (it was never about AI explainability) and
  reorganised into five tabs.
- `pages/2_Assignment_Tasks.py` — same answers, restyled: KPI tiles instead of loose metrics, three-up figure rows,
  consistent tab naming, exports.
- `pages/4_Recommendations.py` — audience selection drives both the generated guidance and a checklist; adds a
  "what would invalidate this" panel.
- `pages/5_Real_Time_Data.py` — auto-refresh off by default (was on, pummelling a free API), explicit empty states,
  chain export.
- `pages/9_Presentation.py` — imports the deck builder explicitly, shows the speaker script in bordered cards.
- `pages/14_Roadmap.py` — split into backlog / done / simplified, with impact badges.
- `utils/ui.py` — rewritten as the app shell: page config, stylesheet injection, sidebar, header, results cache
  keyed on file mtime, guarded sections, export helpers, PDF/HTML viewers.
- All user-facing strings: consistent US-English, consistent currency and percent formatting, "S₀" instead of
  "S0" in prose, hyphenated compounds in headings.

### Removed / merged
- `pages/10_About_Developer.py`, `11_Contact.py`, `12_Documentation.py`, `13_Disclaimer.py` → one
  **About & Docs** page with five tabs. Four near-empty sidebar entries became one.
- Duplicated AI buttons on every page → one collapsible assistant panel per page plus a full chat page.

### Fixed
- `st.download_button(..., label_visibility=...)` raised `TypeError` on newer Streamlit — removed.
- `Model Diagnostics` contained a dead four-iteration loop that computed nothing.
- `Market Data` bound a toggle to the name `live`, shadowing the module-level live-data alias used by the fragment
  decorator.
- `Presentation` relied on a wildcard import to provide `build`/`slides`; now imported explicitly.
- Sidebar footer no longer re-reads the results JSON twice per rerun.

## 1.x — prior submission

Numerical corrections to the original notebook, documented with reproduction steps in
`documentation/CORRECTIONS.md`: Gauss–Legendre quadrature replacing the truncated trapezoid grid, martingale
correction in the QE scheme, Bates jumps simulated in the Monte Carlo, plain-MSE calibration objective, CIR simple-
vs-continuous conventions, CIR σ profile, full-year rate paths, real (not fabricated) payoff histograms, and a
single results file feeding app, notebook and report.
