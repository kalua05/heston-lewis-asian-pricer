"""Cox-Ingersoll-Ross (1985) calibration to the Euribor curve and Monte Carlo of the 12-month rate.

Term structure
    Euribor quotes are simple money-market rates L(tau).  The discount factor is
    P(0, tau) = 1 / (1 + L tau) and the continuously compounded zero rate is
    y(tau) = ln(1 + L tau) / tau.  A cubic spline through the five zero rates gives
    weekly points for 12 months, to which the CIR zero-coupon yield is fitted.
"""
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import differential_evolution, minimize

LABELS = ["1 week", "1 month", "3 months", "6 months", "12 months"]
MAT = np.array([1 / 52, 1 / 12, 3 / 12, 6 / 12, 1.0])
QUOTES = np.array([.648, .679, 1.173, 1.809, 2.556]) / 100          # simple Euribor, decimal
RATES = QUOTES                                                       # backwards-compatible name
KAPPA_B, THETA_B, SIGMA_B = (1e-3, 5.0), (1e-3, 0.10), (1e-3, 1.0)


def simple_to_zero(L, tau):
    return np.log1p(np.asarray(L) * tau) / tau


def zero_to_simple(y, tau):
    return np.expm1(np.asarray(y) * tau) / tau


def term_structure():
    """Discount factors and zero rates implied by the five Euribor quotes."""
    return dict(labels=LABELS, tau=MAT, simple=QUOTES, discount=1 / (1 + QUOTES * MAT), zero=simple_to_zero(QUOTES, MAT))


def weekly_curve(convention="zero"):
    """Cubic-spline interpolation to 52 weekly maturities (1/52 ... 1 year).
    convention='zero' splines the continuously compounded zero rates (default);
    'simple' splines the quoted simple rates directly."""
    t = np.arange(1, 53) / 52
    nodes = simple_to_zero(QUOTES, MAT) if convention == "zero" else QUOTES
    return t, CubicSpline(MAT, nodes)(t)


def cir_zero_params(kappa, sigma, t):
    """A(t), B(t) of the CIR bond price P = A exp(-B r)."""
    g = np.sqrt(kappa ** 2 + 2 * sigma ** 2)
    den = (g + kappa) * np.expm1(g * t) + 2 * g
    return g, den, 2 * np.expm1(g * t) / den


def cir_yield(kappa, theta, sigma, r0, t):
    """Continuously compounded CIR zero yield for maturity t and short rate r0 (array-friendly)."""
    g, den, B = cir_zero_params(kappa, sigma, t)
    lnA = (2 * kappa * theta / sigma ** 2) * np.log(2 * g * np.exp((kappa + g) * t / 2) / den)
    return -(lnA - B * r0) / t


def _rmse(p, y, t, r0):
    return float(np.sqrt(np.mean((y - cir_yield(p[0], p[1], p[2], r0, t)) ** 2)))


def calibrate_cir(convention="zero", sigma_tol_bp=0.02, seed=0):
    """Least-squares CIR fit to the weekly curve with r0 = 1-week rate and the Feller constraint 2*kappa*theta >= sigma^2.

    The curve barely constrains sigma (see ``profile``): the reported sigma is the midpoint of the plateau of
    sigma values whose RMSE is within ``sigma_tol_bp`` basis points of the best fit.
    """
    t, y = weekly_curve(convention); r0 = float(y[0])
    prof = []
    for s in np.round(np.arange(0.01, 0.4501, 0.01), 3):
        best = min((minimize(lambda z: _rmse((z[0], z[1], s), y, t, r0) + 1e3 * max(0.0, s ** 2 - 2 * z[0] * z[1]),
                             x0, bounds=[KAPPA_B, THETA_B], method="L-BFGS-B") for x0 in
                    ([.5, .03], [1., .05], [3., .04], [.2, .08], [.1, .02])), key=lambda o: o.fun)
        k, th = best.x
        prof.append((float(s), float(k), float(th), _rmse((k, th, s), y, t, r0) * 1e4, 2 * k * th - s ** 2))
    prof = np.array(prof)
    feas = prof[prof[:, 4] >= -1e-9]
    best_bp = feas[:, 3].min()
    plateau = feas[feas[:, 3] <= best_bp + sigma_tol_bp]
    row = plateau[len(plateau) // 2]
    s_hat = float(row[0]); k0, th0 = float(row[1]), float(row[2])
    loc = minimize(lambda z: _rmse((z[0], z[1], s_hat), y, t, r0), [k0, th0], bounds=[KAPPA_B, THETA_B], method="L-BFGS-B")
    k, th = [float(v) for v in loc.x]
    if 2 * k * th < s_hat ** 2: k, th = k0, th0
    model = cir_yield(k, th, s_hat, r0, t)
    return dict(kappa=k, theta=th, sigma=s_hat, r0=r0, t=t, market=y, model=model,
                rmse=_rmse((k, th, s_hat), y, t, r0), rmse_bp=_rmse((k, th, s_hat), y, t, r0) * 1e4,
                feller=2 * k * th - s_hat ** 2, convention=convention,
                profile=prof, plateau=(float(plateau[:, 0].min()), float(plateau[:, 0].max())))


def simulate_cir_paths(r0, kappa, theta, sigma, T=1.0, n_steps=250, n=100_000, seed=42,
                       tau=1.0, qs=(0.005, 0.025, 0.05, 0.5, 0.95, 0.975, 0.995), n_sample=40):
    """Exact CIR transition (non-central chi-square), daily steps, ``n`` paths.

    At every date t the 12-month Euribor is L12(t) = expm1(y(r_t, tau)) with y the CIR zero yield
    (an affine function of r_t).  Returns per-day mean/quantiles, path-wise min/max over the year,
    the terminal short rates / 12M rates and a few sample paths.
    """
    rng = np.random.default_rng(seed)
    dt = T / n_steps; e = np.exp(-kappa * dt); c = sigma ** 2 * (1 - e) / (4 * kappa); dfree = 4 * kappa * theta / sigma ** 2
    g, den, B = cir_zero_params(kappa, sigma, tau)
    lnA = (2 * kappa * theta / sigma ** 2) * np.log(2 * g * np.exp((kappa + g) * tau / 2) / den)
    to12 = lambda r: np.expm1((-lnA + B * r) / tau) * (1 / tau)
    r = np.full(n, float(r0)); L = to12(r)
    days = np.arange(n_steps + 1); mean = [L.mean()]; quant = [np.quantile(L, qs)]
    pmin, pmax = L.copy(), L.copy(); samples = [L[:n_sample].copy()]
    for _ in range(n_steps):
        r = c * rng.noncentral_chisquare(dfree, r * e / c)
        L = to12(r); mean.append(L.mean()); quant.append(np.quantile(L, qs))
        np.minimum(pmin, L, out=pmin); np.maximum(pmax, L, out=pmax); samples.append(L[:n_sample].copy())
    return dict(days=days, t=days / n_steps * T, mean=np.array(mean), quantiles=np.array(quant), qs=np.array(qs),
                path_min=pmin, path_max=pmax, terminal_r=r, terminal_L12=L, samples=np.array(samples),
                analytic_mean_r=float(theta + (r0 - theta) * np.exp(-kappa * T)))


def simulate_cir_exact(r0, kappa, theta, sigma, T=1.0, n_steps=250, n=100_000, seed=42):
    """Terminal short rates only (kept for backwards compatibility)."""
    return simulate_cir_paths(r0, kappa, theta, sigma, T, n_steps, n, seed, n_sample=1)["terminal_r"]
