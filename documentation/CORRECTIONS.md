# Corrections and verification log

Audit of the uploaded project against the MScFE 622 GWP1 brief. Each item was reproduced numerically before it was changed.

## Numerical and modelling fixes
| # | Problem found | Fix | Evidence |
|---|---|---|---|
| 1 | Fourier integrals truncated at u = 200 on a trapezoid grid: errors up to $0.02–0.04 in short-maturity / high vol-of-vol corners, and 2–5× slower | Composite Gauss–Legendre on [0, 400], Carr–Madan phase merged with log-moneyness | 9,240 test prices vs adaptive quadrature: worst error $0.004 (Lewis), $0.009 (Carr–Madan); 0.47 ms per 10-strike evaluation |
| 2 | QE Monte Carlo had no martingale correction (E[S_T] ≠ forward); z = −2.2 vs the closed form at 70 days | Andersen (2008) martingale-corrected log-price step | MC vs Fourier within ±1.5σ in 27 of 28 checks; Euler shows z up to 14 |
| 3 | Bates priced with Heston Monte Carlo (no jumps) for the 70-day put | Jumps simulated with exact compensator | MC vs Fourier agree |
| 4 | Calibration loss silently included a Feller penalty, contradicting the brief's "regular MSE"; reported MSE mixed in the penalty | Plain MSE by default; Feller penalty optional and reported separately; fixed seeds, larger search | Penalty changes MSE by 0.1% but parameters completely |
| 5 | CIR: Euribor simple rates fed to a continuously compounded model; spline on raw quotes | Discount factors 1/(1+Lτ), zero rates ln(1+Lτ)/τ, weekly spline; results converted back to simple 12M rates | 3 bp at 12 months |
| 6 | CIR σ was just the optimiser's starting value (fit RMSE identical for σ from 0.01 to 0.3) and the reported RMSE included the penalty | Profile over σ, plateau midpoint, σ-sensitivity table, true RMSE | Figure in Step 3a |
| 7 | CIR simulation returned only terminal short rates; question (i) asks for the range over the year and (iii) for the pricing impact was missing | 100,000 exact daily paths, daily bands, path extremes, expected value (analytic check), re-pricing of both products | Tests |
| 8 | Live Simulation page histogram was fabricated (`normal(a, …)`), upload calibrated all maturities as one | Real simulated payoffs; maturity selector with error handling | — |
| 9 | Home page used whichever maturity the user selected for the "20-day Asian"; slide deck and report held stale hard-coded numbers; shipped PDF was the uncorrected 2025 submission (including code cells) | Headline results always come from the 15-day calibration; deck/report/app read one results file; new answers-only PDF | — |
| 10 | Relative paths (`data/...`) broke when launched from another directory; deprecated `use_container_width`; unpinned dependencies | `utils/paths.py`, `width="stretch"`, bounded requirements, Docker health check, non-root user | — |

## Findings about the data (not code bugs)
* **Calls and puts violate put–call parity** (up to $2.0 at 15 days, $3.2 at 60 days; 60-day calls non-monotone). The irreducible MSE floor is ≈0.21 (15 d) and ≈1.27 (60 d); fits reach 0.246 and 1.34–1.36. Positive ρ at 60 days is an artefact of this.
* Parameters are weakly identified (different seeds, same MSE). Prices are stable; that is why the report compares prices and shows seed/penalty robustness.

## Not changed / limitations
* 70-day put uses 60-day parameters (nearest maturity). Quotes at 120 days are not used in Step 2.
* CIR: curve spans 12 months only; κ, θ extrapolate; σ is not identified.
