"""Calibration of Heston (1993) and Bates (1996) to vanilla option quotes.

Objective (per the brief): the *regular* mean squared error between model and market
prices.  Calls are priced with the closed-form Fourier call and puts with put-call
parity.  An optional Feller penalty (``feller='penalty'``) is available as a robustness
check but is OFF by default so that the reported MSE is exactly the objective optimised.
"""
import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize

from .lewis import model_price
from .paths import DATA_FILE

B_H = [(1e-3, 1), (1e-2, 8), (1e-3, 1), (1e-2, 2), (-.99, .99)]
B_B = B_H + [(1e-3, 3), (-.5, .5), (1e-3, .5)]
BOUNDS = B_H
NAMES = {
    "heston": ["v0", "kappa", "theta", "sigma", "rho"],
    "bates": ["v0", "kappa", "theta", "sigma", "rho", "lambda", "mu_J", "delta_J"],
}
REQUIRED_COLUMNS = {"Strike", "Price", "Type"}
FELLER_WEIGHT = 1e3


def _validate_quotes(df):
    """Reject incomplete or invalid option quotes before starting an optimizer."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Option quotes must be provided as a pandas DataFrame.")
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Option data is missing required columns: {', '.join(sorted(missing))}.")
    if df.empty:
        raise ValueError("No option quotes are available for this maturity.")
    if len(df) < 2:
        raise ValueError("At least two option quotes are required for calibration.")
    for col in ("Strike", "Price"):
        values = pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)
        if not np.all(np.isfinite(values)):
            raise ValueError(f"Option {col.lower()} values must all be finite numbers.")
        if np.any(values <= 0):
            raise ValueError(f"Option {col.lower()} values must be positive.")
    types = df["Type"].astype(str).str.upper()
    if not types.isin(["C", "P"]).all():
        raise ValueError("Option Type values must be 'C' (call) or 'P' (put).")


def load_data(path=None, days=None):
    """Load the quotes for one maturity (or all maturities if ``days`` is None)."""
    path = path or DATA_FILE
    df = pd.read_excel(path) if str(path).lower().endswith((".xlsx", ".xls")) else pd.read_csv(path)
    if "Days to maturity" not in df.columns:
        raise ValueError("Option data must contain a 'Days to maturity' column.")
    maturity = pd.to_numeric(df["Days to maturity"], errors="coerce")
    if days is None:
        selected = df.copy().reset_index(drop=True)
    else:
        selected = df.loc[maturity == days].copy().reset_index(drop=True)
        if selected.empty:
            available = sorted(maturity.dropna().unique().tolist())
            raise ValueError(f"No quotes found for {days} days to maturity. Available maturities: {available}.")
    _validate_quotes(selected)
    selected["Type"] = selected["Type"].astype(str).str.upper()
    return selected


def parity_table(df, S, r, q, T):
    """Put-call parity diagnostic: (C - P) - (S e^{-qT} - K e^{-rT}) at common strikes."""
    c = df[df.Type == "C"].set_index("Strike").Price
    p = df[df.Type == "P"].set_index("Strike").Price
    k = c.index.intersection(p.index)
    out = pd.DataFrame({"Call": c[k], "Put": p[k]})
    out["C-P"] = out.Call - out.Put
    out["S-Ke^-rT"] = S * np.exp(-q * T) - k.values * np.exp(-r * T)
    out["Violation"] = out["C-P"] - out["S-Ke^-rT"]
    return out.reset_index()


def mse(p, df, S, r, q, T, model="heston", method="lewis"):
    """Regular mean squared price error (what the brief asks to minimise)."""
    _validate_quotes(df)
    if model not in NAMES:
        raise ValueError(f"Unknown model {model!r}; choose 'heston' or 'bates'.")
    prices = model_price(S, df["Strike"].to_numpy(dtype=float), T, r, q, p,
                         df["Type"].to_numpy(), model, method)
    return float(np.mean((prices - df["Price"].to_numpy(dtype=float)) ** 2))


def feller_gap(p):
    """2*kappa*theta - sigma^2 (>= 0 means the Feller condition holds)."""
    return float(2 * p[1] * p[2] - p[3] ** 2)


def _objective(p, df, S, r, q, T, model, method, feller):
    error = mse(p, df, S, r, q, T, model, method)
    if feller == "penalty":
        error += FELLER_WEIGHT * max(0.0, -feller_gap(p))
    return error


def calibrate(df, S, r, q, T, model="heston", method="lewis", seed=0,
              maxiter=200, popsize=20, bounds=None, feller="none"):
    """Global differential evolution + bounded L-BFGS-B polish.

    Returns a dict with ``mse`` (regular MSE of the fit), ``objective`` (what was minimised;
    equals ``mse`` unless ``feller='penalty'``), the fitted prices, and the list of
    parameters sitting on a bound (a sign of weak identification).
    """
    _validate_quotes(df)
    if model not in NAMES:
        raise ValueError(f"Unknown model {model!r}; choose 'heston' or 'bates'.")
    if method not in ("lewis", "cm"):
        raise ValueError("method must be 'lewis' or 'cm'.")
    if feller not in ("none", "penalty"):
        raise ValueError("feller must be 'none' or 'penalty'.")
    if not np.isfinite(S) or S <= 0 or not np.isfinite(T) or T <= 0:
        raise ValueError("Spot and maturity must be finite and positive.")
    bd = bounds or (B_H if model == "heston" else B_B)
    if len(bd) != len(NAMES[model]):
        raise ValueError(f"{model} calibration requires {len(NAMES[model])} parameter bounds.")
    args = (df, S, r, q, T, model, method, feller)
    de = differential_evolution(_objective, bd, args=args, seed=seed, maxiter=maxiter,
                                popsize=popsize, tol=1e-10, atol=0, polish=False)
    local = minimize(_objective, de.x, args=args, method="L-BFGS-B", bounds=bd)
    best = local if local.fun <= de.fun else de
    x = np.asarray(best.x, float)
    fitted = model_price(S, df["Strike"].to_numpy(dtype=float), T, r, q, x,
                         df["Type"].to_numpy(), model, method)
    res = fitted - df["Price"].to_numpy(dtype=float)
    fit_mse = float(np.mean(res ** 2))
    at_bounds = [n for n, v, (lo, hi) in zip(NAMES[model], x, bd)
                 if v - lo < 1e-3 * (hi - lo) or hi - v < 1e-3 * (hi - lo)]
    return {
        "params": x, "mse": fit_mse, "rmse": float(np.sqrt(fit_mse)), "mae": float(np.mean(np.abs(res))),
        "objective": float(best.fun), "model": fitted, "residuals": res,
        "feller": feller_gap(x), "at_bounds": at_bounds, "names": NAMES[model],
        "method": method, "model_name": model, "feller_mode": feller, "seed": seed,
        "n_eval": int(de.nfev + local.nfev),
    }
