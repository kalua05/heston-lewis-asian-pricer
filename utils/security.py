"""Security helpers: input validation, upload checks, per-session throttling, global compute/AI budgets.

None of this makes a public web app 'unhackable'; it removes the practical abuse paths of this app
(oversized uploads, absurd inputs, CPU/memory exhaustion, unlimited paid-API calls, prompt injection).
"""
import datetime as dt, threading
import numpy as np, pandas as pd, streamlit as st

MAX_UPLOAD_ROWS, MAX_TEXT, MAX_AI_CHARS = 200, 2000, 1000
MAX_AI_PER_SESSION, MAX_AI_PER_DAY = 30, 400
MAX_HEAVY_PER_SESSION_MIN = 12          # calibrations / big simulations per session per minute window
MC_BUDGET = 20_000_000                  # paths x steps per Monte Carlo call
ss = st.session_state

@st.cache_resource
def _state():
    return dict(sem=threading.BoundedSemaphore(2), lock=threading.Lock(), day=dt.date.today(), ai=0)

def clip(text, n=MAX_TEXT):
    """Trim untrusted text and drop control characters."""
    t = "".join(ch for ch in str(text or "") if ch == "\n" or ch >= " ")
    return t[:n]

def mc_paths(n, steps):
    """Cap paths so that paths x steps stays within the memory/CPU budget."""
    return int(max(1000, min(int(n), MC_BUDGET // max(int(steps), 1))))

def heavy(label="calculation"):
    """Context manager: at most 2 heavy jobs run at once on the server and each session is rate limited."""
    class _H:
        def __enter__(self_):
            now = __import__("time").time(); hist = [t for t in ss.get("_heavy", []) if now - t < 60]
            if len(hist) >= MAX_HEAVY_PER_SESSION_MIN:
                st.warning("Too many heavy calculations in a minute – please wait a little."); st.stop()
            ss["_heavy"] = hist + [now]
            if not _state()["sem"].acquire(blocking=False):
                st.warning(f"The server is busy with other {label}s – try again in a moment."); st.stop()
            return self_
        def __exit__(self_, *a): _state()["sem"].release(); return False
    return _H()

def ai_allowed():
    """Per-session and per-day cap on paid AI calls. Returns (ok, message)."""
    s = _state()
    with s["lock"]:
        if s["day"] != dt.date.today(): s["day"], s["ai"] = dt.date.today(), 0
        if ss.get("_ai_n", 0) >= MAX_AI_PER_SESSION: return False, "Session AI limit reached."
        if s["ai"] >= MAX_AI_PER_DAY: return False, "Daily AI limit reached; try again tomorrow."
        s["ai"] += 1; ss["_ai_n"] = ss.get("_ai_n", 0) + 1
    return True, ""

def validate_upload(df):
    """Validate an uploaded option-quote table. Returns (clean_df, error)."""
    need = ["Days to maturity", "Strike", "Price", "Type"]
    if any(c not in df.columns for c in need): return None, f"CSV needs the columns: {', '.join(need)}."
    if len(df) == 0 or len(df) > MAX_UPLOAD_ROWS: return None, f"Use between 1 and {MAX_UPLOAD_ROWS} rows."
    d = df[need].copy()
    for c in ["Days to maturity", "Strike", "Price"]: d[c] = pd.to_numeric(d[c], errors="coerce")
    d["Type"] = d["Type"].astype(str).str.strip().str.upper().str[:1]
    n0 = len(d); d = d.dropna()
    if len(d) == 0 or len(d) < n0: return None, "Some rows contain missing or non-numeric values."
    if not np.isfinite(d[["Days to maturity", "Strike", "Price"]].to_numpy()).all(): return None, "Non-finite numbers found."
    if (d["Type"].isin(["C", "P"]) == False).any(): return None, "Type must be C or P."
    if not d["Days to maturity"].between(1, 750).all(): return None, "Days to maturity must be between 1 and 750."
    if not d["Strike"].between(1, 5000).all() or not d["Price"].between(0, 5000).all(): return None, "Strike or price out of range."
    if d["Days to maturity"].nunique() > 12: return None, "Too many different maturities (max 12)."
    d["Days to maturity"] = d["Days to maturity"].astype(int)
    return d.reset_index(drop=True), None
