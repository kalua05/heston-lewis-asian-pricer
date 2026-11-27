"""Fourier pricing of European options: Lewis (2001) and Carr-Madan (1999).

Both formulas integrate a smooth function over u in [0, U_MAX].  The integral is
evaluated with composite Gauss-Legendre quadrature (accurate to ~1e-4 dollars on
the quotes used here, and ~3x faster than a dense trapezoid grid).  Put prices
always come from put-call parity, as the brief prefers.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.optimize import brentq
from scipy.stats import norm

from .models import cf_X

U_MAX, PANEL, ORDER = 400.0, 5.0, 16


def _gauss_legendre_grid(u_max=U_MAX, panel=PANEL, order=ORDER):
    x, w = leggauss(order)
    edges = np.arange(0.0, u_max + panel / 2, panel)
    a, b = edges[:-1, None], edges[1:, None]
    return ((b - a) / 2 * x + (a + b) / 2).ravel(), ((b - a) / 2 * w).ravel()


_U, _W = _gauss_legendre_grid()
U_PLOT = np.linspace(1e-8, 60.0, 1500)          # for illustrative integrand plots only


def lewis_call(S, K, T, r, q, p, model="heston"):
    """Lewis (2001) eq. 3.11 (nu = 1/2).  p = (v0, kappa, theta, sigma, rho[, lam, mu_J, delta_J]).
    K may be an array.  C = S e^{-qT} - sqrt(S K) e^{-(r+q)T/2}/pi * int_0^inf Re[e^{iuk} phi(u - i/2)]/(u^2+1/4) du."""
    K = np.atleast_1d(np.asarray(K, float))
    k = np.log(S / K) + (r - q) * T
    phi = cf_X(_U - 0.5j, T, p, model)
    f = np.real(np.exp(1j * np.outer(k, _U)) * phi) / (_U ** 2 + 0.25)
    return S * np.exp(-q * T) - np.sqrt(S * K) * np.exp(-(r + q) * T / 2) / np.pi * (f @ _W)


def cm_call(S, K, T, r, q, p, model="heston", alpha=1.5):
    """Carr-Madan (1999) damped call transform, c(k) = e^{-alpha k}/pi * int_0^inf Re[e^{-ivk} psi(v)] dv."""
    K = np.atleast_1d(np.asarray(K, float))
    lnK, m = np.log(K), np.log(S) + (r - q) * T
    z = _U - (alpha + 1) * 1j
    # E[exp(i z ln S_T)] = exp(i z m) phi_X(z); the real part of the phase is merged with e^{-iv lnK}
    # so the integrand only oscillates at the (small) log-moneyness frequency.
    psi = np.exp(-r * T) * np.exp((alpha + 1) * m) * cf_X(z, T, p, model) / (
        alpha ** 2 + alpha - _U ** 2 + 1j * (2 * alpha + 1) * _U)
    f = np.real(np.exp(1j * np.outer(m - lnK, _U)) * psi)
    return np.exp(-alpha * lnK) / np.pi * (f @ _W)


def model_price(S, K, T, r, q, p, typ, model="heston", method="lewis"):
    """Call/put prices (puts via put-call parity).  typ is 'C'/'P' (scalar or array matching K)."""
    c = (lewis_call if method == "lewis" else cm_call)(S, K, T, r, q, p, model)
    K = np.atleast_1d(np.asarray(K, float))
    put = c - S * np.exp(-q * T) + K * np.exp(-r * T)
    return np.where(np.asarray(typ) == "C", c, put)


def integrand(S, K, T, r, q, p, model="heston"):
    """Lewis integrand on a plotting grid (illustration only)."""
    k = np.log(S / K) + (r - q) * T
    return U_PLOT, np.real(np.exp(1j * U_PLOT * k) * cf_X(U_PLOT - 0.5j, T, p, model)) / (U_PLOT ** 2 + 0.25)


def bs(S, K, T, r, q, s, typ):
    d1 = (np.log(S / K) + (r - q + .5 * s * s) * T) / (s * np.sqrt(T)); d2 = d1 - s * np.sqrt(T)
    if typ == "C":
        return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)


def implied_vol(price, S, K, T, r, q, typ):
    """Black-Scholes implied volatility by bracketed Brent search (NaN if the price is outside no-arbitrage bounds)."""
    try:
        return brentq(lambda s: bs(S, K, T, r, q, s, typ) - price, 1e-4, 5.0)
    except Exception:
        return np.nan


def greeks(S, K, T, r, q, p, typ="C", h=1e-2):
    """Finite-difference Greeks of the model price (delta, gamma, theta per year, rho per 1%, dP/dv0)."""
    f = lambda S_=S, T_=T, r_=r, p_=p: float(model_price(S_, K, T_, r_, q, p_, typ)[0])
    d = (f(S + h * S) - f(S - h * S)) / (2 * h * S)
    g = (f(S + h * S) - 2 * f() + f(S - h * S)) / (h * S) ** 2
    th = (f(T_=T - 1 / 250) - f()) * 250 if T > 2 / 250 else None
    rho_ = (f(r_=r + 1e-4) - f(r_=r - 1e-4)) / 2e-4 / 100
    up = (p[0] * 1.01,) + tuple(p[1:]); dn = (p[0] * .99,) + tuple(p[1:])
    return dict(delta=d, gamma=g, theta_per_year=th, rho_per_1pct=rho_, dPrice_dv0=(f(p_=up) - f(p_=dn)) / (0.02 * p[0]))
