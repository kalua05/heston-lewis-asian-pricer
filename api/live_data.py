import os
from typing import Optional
import requests
import pandas as pd
import streamlit as st


def _ticker_history(ticker: str, period: str = "5d"):
    import yfinance as yf
    return yf.Ticker(ticker)


@st.cache_data(ttl=5, show_spinner=False)
def market_snapshot(ticker: str = "SM"):
    import yfinance as yf

    def last_close(symbol):
        history = yf.Ticker(symbol).history(period="5d", auto_adjust=False)
        if history is None or history.empty:
            return None
        return float(history["Close"].iloc[-1])

    ticker = ticker or "SM"
    ticker_obj = yf.Ticker(ticker)
    history = ticker_obj.history(period="5d", auto_adjust=False)
    spot = float(history["Close"].iloc[-1]) if history is not None and not history.empty else None
    previous = float(history["Close"].iloc[-2]) if history is not None and len(history) >= 2 else None
    change_pct = ((spot / previous) - 1.0) * 100 if spot is not None and previous else None

    return {
        "ticker": ticker,
        "spot": spot,
        "previous": previous,
        "change_pct": change_pct,
        "spx": last_close("^GSPC"),
        "vix": last_close("^VIX"),
        "tnx": last_close("^TNX"),
        "timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
    }


@st.cache_data(ttl=5, show_spinner=False)
def spot(ticker: str = "SM"):
    try:
        value = market_snapshot(ticker).get("spot")
        return float(value) if value is not None else 232.90
    except Exception:
        return 232.90


def safe_spot(ticker: str = "SM"):
    try:
        return spot(ticker)
    except Exception:
        return 232.90


@st.cache_data(ttl=300)
def expiries(tk="SM"):
    import yfinance as yf
    return list(yf.Ticker(tk).options)


@st.cache_data(ttl=300)
def chain(expiry, tk="SM"):
    import yfinance as yf
    c = yf.Ticker(tk).option_chain(expiry)
    d = pd.concat([c.calls.assign(Type="C"), c.puts.assign(Type="P")])
    d["Price"] = (d["bid"] + d["ask"])/2
    return d[(d["bid"] > 0) & (d["ask"] > 0)][["strike", "Price", "Type", "impliedVolatility"]].rename(columns={"strike": "Strike"})


@st.cache_data(ttl=3600)
def risk_free(default=0.015):
    key = os.environ.get("FRED_API_KEY")
    if not key:
        try:
            key = st.secrets["FRED_API_KEY"]
        except Exception:
            key = None
    try:
        if key:
            j = requests.get("https://api.stlouisfed.org/fred/series/observations", timeout=8,
                            params={"series_id": "DGS3MO", "api_key": key, "file_type": "json",
                                    "sort_order": "desc", "limit": 5}).json()
            for observation in j["observations"]:
                if observation["value"] != ".":
                    return float(observation["value"])/100
    except Exception:
        pass
    return default


@st.cache_data(ttl=300)
def market_context():
    import yfinance as yf
    out = {}
    for name, symbol in {"SPX": "^GSPC", "VIX": "^VIX", "TNX": "^TNX"}.items():
        try:
            history = yf.Ticker(symbol).history(period="5d")
            out[name] = float(history["Close"].iloc[-1]) if not history.empty else None
        except Exception:
            out[name] = None
    return out


@st.cache_data(ttl=600)
def news(tk="SM", n=5):
    import yfinance as yf
    out = []
    for item in (yf.Ticker(tk).news or [])[:n]:
        content = item.get("content", item)
        out.append({"title": str(content.get("title") or "")[:200],
                    "publisher": str((content.get("provider") or {}).get("displayName") or "")[:60]})
    return out


@st.cache_data(ttl=3600)
def dividend_yield(tk="SM"):
    import yfinance as yf
    try:
        value = yf.Ticker(tk).info.get("dividendYield") or 0.0
        return float(value/100 if value > 0.5 else value)
    except Exception:
        return 0.0
