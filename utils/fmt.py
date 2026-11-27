"""Number formatting shared by the app, the notebook and the report.

Every user-facing number goes through one of these helpers so units, decimals and
sign conventions are identical on every page.
"""
from __future__ import annotations

import math

import numpy as np

DASH = "—"


def _finite(x) -> bool:
    try:
        return math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def money(x, digits: int = 2, dash: str = DASH) -> str:
    """Dollar amount, tabular-numerals friendly."""
    return f"${x:,.{digits}f}" if _finite(x) else dash


def signed_money(x, digits: int = 2) -> str:
    return f"{x:+,.{digits}f}" if _finite(x) else DASH


def num(x, digits: int = 2) -> str:
    return f"{x:,.{digits}f}" if _finite(x) else DASH


def pct(x, digits: int = 2, signed: bool = False) -> str:
    if not _finite(x):
        return DASH
    return f"{x:+.{digits}%}" if signed else f"{x:.{digits}%}"


def bp(x, digits: int = 1, signed: bool = False) -> str:
    if not _finite(x):
        return DASH
    v = float(x) * 1e4
    return f"{v:+,.{digits}f} bp" if signed else f"{v:,.{digits}f} bp"


def iv(x, digits: int = 2) -> str:
    """Implied volatility stored as a decimal (0.21 -> 21.00%)."""
    return pct(x, digits)


def ratio(x, digits: int = 2) -> str:
    return f"{x:,.{digits}f}×" if _finite(x) else DASH


def delta_span(lo, hi, digits: int = 2) -> str:
    """'[4.71, 4.73]' style confidence interval."""
    if not (_finite(lo) and _finite(hi)):
        return DASH
    return f"[{lo:,.{digits}f}, {hi:,.{digits}f}]"


def arrow(x) -> str:
    """Coloured span for a change value (used inside KPI subtitles)."""
    if not _finite(x):
        return ""
    cls, glyph = ("up", "▲") if float(x) >= 0 else ("down", "▼")
    return f"<span class='{cls}'>{glyph} {abs(float(x)):,.2f}</span>"


def describe_change(x, digits: int = 2, unit: str = "%") -> str:
    if not _finite(x):
        return DASH
    cls, glyph = ("up", "▲") if float(x) >= 0 else ("down", "▼")
    return f"<span class='{cls}'>{glyph} {abs(float(x)):,.{digits}f}{unit}</span>"


def to_float(x, default=float("nan")) -> float:
    """Best-effort float conversion that never raises."""
    try:
        v = float(x)
        return v if np.isfinite(v) else default
    except (TypeError, ValueError):
        return default
