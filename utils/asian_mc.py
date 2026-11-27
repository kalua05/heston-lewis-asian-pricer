"""Risk-neutral Monte Carlo for Heston / Bates payoffs.

* ``scheme='qe'``   Andersen (2008) quadratic-exponential variance scheme with the
                    martingale-corrected log-price step (E[S_t] equals the forward).
* ``scheme='euler'`` full-truncation Euler (comparison scheme).
* Bates (1996) jumps are added to the log-price with the exact compensator.
* Antithetic variates; the standard error uses the antithetic-pair averages.
* Asian payoff = max(mean(S_0, S_1, ..., S_n) - K, 0): today's price S_0 IS in the
  average (n_steps + 1 fixings), as required by the brief.
"""
import numpy as np
from scipy.special import ndtri

PAYOFFS = ("asian_call", "asian_put", "call", "put")


def _payoff(kind, K, avg, last):
    if kind == "asian_call": return np.maximum(avg - K, 0.0)
    if kind == "asian_put": return np.maximum(K - avg, 0.0)
    if kind == "call": return np.maximum(last - K, 0.0)
    if kind == "put": return np.maximum(K - last, 0.0)
    raise ValueError(f"payoff must be one of {PAYOFFS}")


def _qe_step(v, u, kappa, theta, sigma, dt, psic):
    """One QE variance step; returns (v_next, M-correction ingredients)."""
    e = np.exp(-kappa * dt)
    m = theta + (v - theta) * e
    s2 = v * sigma ** 2 * e / kappa * (1 - e) + theta * sigma ** 2 / (2 * kappa) * (1 - e) ** 2
    psi = s2 / m ** 2
    quad = psi <= psic
    inv = 2.0 / np.maximum(psi, 1e-12)
    b2 = np.maximum(inv - 1 + np.sqrt(inv * np.maximum(inv - 1, 0)), 0)
    a = m / (1 + b2)
    vq = a * (np.sqrt(b2) + ndtri(np.clip(u, 1e-12, 1 - 1e-12))) ** 2
    pr = (psi - 1) / (psi + 1)
    beta = (1 - pr) / m
    ve = np.where(u <= pr, 0.0, np.log((1 - pr) / np.maximum(1 - u, 1e-12)) / beta)
    return np.where(quad, vq, ve), (quad, a, b2, pr, beta)


def simulate(S0, K, T, r, q, p, n_steps, n_paths=100_000, seed=42, model="heston",
             payoff="asian_call", scheme="qe", antithetic=True, psic=1.5, return_payoffs=False,
             include_s0=True):
    """Price a payoff under Heston (p has 5 entries) or Bates (8 entries).

    ``include_s0=False`` drops today's price from the average (only used to show the size of that error).
    Returns (price, standard_error, (ci_low, ci_high)) and, optionally, the discounted payoffs.
    """
    if payoff not in PAYOFFS: raise ValueError(f"payoff must be one of {PAYOFFS}")
    if scheme not in ("qe", "euler"): raise ValueError("scheme must be 'qe' or 'euler'")
    v0, kappa, theta, sigma, rho = p[:5]
    lam, mu_j, dl_j = (p[5:8] if model == "bates" else (0.0, 0.0, 0.0))
    kbar = np.exp(mu_j + .5 * dl_j ** 2) - 1
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    n = n_paths // 2 if antithetic else n_paths
    sg = np.array([1.0, -1.0] if antithetic else [1.0])[:, None]
    shape = (len(sg), n)
    lnS = np.full(shape, np.log(S0)); V = np.full(shape, float(v0)); tot = np.full(shape, float(S0) if include_s0 else 0.0)
    if scheme == "qe":
        g = .5
        K1 = g * dt * (kappa * rho / sigma - .5) - rho / sigma
        K2 = g * dt * (kappa * rho / sigma - .5) + rho / sigma
        K3 = K4 = g * dt * (1 - rho ** 2)
        K0 = -rho * kappa * theta * dt / sigma
        A = K2 + .5 * K4
    for _ in range(n_steps):
        U = rng.random(n); Z = rng.standard_normal(n); Z1 = rng.standard_normal(n)
        u = np.where(sg > 0, U, 1 - U); z = sg * Z
        if scheme == "qe":
            vn, (quad, a, b2, pr, beta) = _qe_step(V, u, kappa, theta, sigma, dt, psic)
            with np.errstate(all="ignore"):
                Mq = np.exp(A * b2 * a / (1 - 2 * A * a)) / np.sqrt(1 - 2 * A * a)
                Me = pr + beta * (1 - pr) / (beta - A)
                M = np.where(quad, Mq, Me)
                ok = np.where(quad, 2 * A * a < 1, A < beta) & np.isfinite(M) & (M > 0)
                k0 = np.where(ok, -np.log(np.where(ok, M, 1.0)) - (K1 + .5 * K3) * V, K0)
            dlog = (r - q) * dt + k0 + K1 * V + K2 * vn + np.sqrt(np.maximum(K3 * V + K4 * vn, 0)) * z
            V = vn
        else:
            vp = np.maximum(V, 0)
            z2 = sg * (rho * Z + np.sqrt(1 - rho ** 2) * Z1)      # price shock, correlated with variance shock Z
            dlog = (r - q - .5 * vp) * dt + np.sqrt(vp * dt) * z2
            V = V + kappa * (theta - vp) * dt + sigma * np.sqrt(vp * dt) * sg * Z
        if lam > 0:
            N = rng.poisson(lam * dt, size=n)
            Zj = sg * rng.standard_normal(n)
            dlog = dlog + mu_j * N + dl_j * np.sqrt(N) * Zj - lam * kbar * dt
        lnS = lnS + dlog
        tot += np.exp(lnS)
    S_T = np.exp(lnS)
    pay = _payoff(payoff, K, tot / (n_steps + (1 if include_s0 else 0)), S_T).mean(axis=0) * np.exp(-r * T)   # average antithetic pairs
    m = float(pay.mean()); se = float(pay.std(ddof=1) / np.sqrt(len(pay)))
    out = (m, se, (m - 1.96 * se, m + 1.96 * se))
    return (out, pay) if return_payoffs else out


def asian_call_qe(S0, K, T, r, q, p, n_steps, n_paths=100_000, seed=42, psic=1.5, kind="asian", model=None):
    """QE Monte Carlo. kind: 'asian' (Asian call, S0 in the average), 'put' (European put), 'call' (European call)."""
    model = model or ("bates" if len(p) == 8 else "heston")
    payoff = {"asian": "asian_call", "put": "put", "call": "call"}.get(kind, kind)
    return simulate(S0, K, T, r, q, p, n_steps, n_paths, seed, model, payoff, "qe", True, psic)


def asian_call_mc(S0, K, T, r, q, p, n_steps, n_paths=100_000, seed=42, antithetic=True, model=None):
    """Full-truncation Euler Monte Carlo for the Asian call (S0 included in the average)."""
    model = model or ("bates" if len(p) == 8 else "heston")
    return simulate(S0, K, T, r, q, p, n_steps, n_paths, seed, model, "asian_call", "euler", antithetic)
