import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import *
from utils.theme import badge, callout, empty_state, kpi_row, page_header, panel

setup("Dashboard", "🏠")

R_ = get_results()
M = R_["meta"]
s1, s2, s3 = R_["step1c"], R_["step2c"], R_["step3b"]
put = s2["models"][s2["headline"]]["mc"]

st.markdown(
    page_header(
        "SM Energy options dashboard",
        "A calibrated Heston / Bates pricing desk for SM Energy options: Fourier pricing with "
        "Lewis (2001) and Carr–Madan (1999), Monte Carlo for Asian and European payoffs, and CIR "
        "scenarios for the 12-month Euribor.",
        kicker="MScFE 622 · Group Work Project 1",
        meta=[badge(f"Spot ${M['spot']:.2f}", "accent"),
              badge(f"r = {M['r']:.2%}", "info"),
              badge(f"{M['n_mc']:,} MC paths", "info"),
              badge("AI online" if AI_ON() else "AI offline", "accent" if AI_ON() else "neutral")],
    ),
    unsafe_allow_html=True,
)

st.markdown(
    kpi_row([
        ("Asian call · 20d ATM", money(s1["qe"]["price"], 4), f"Fair value · 95% CI {delta_span(*s1['qe']['ci'], 3)}", "accent"),
        ("Client price (+4% fee)", money(s1["qe"]["client"], 4), f"Fee {money(s1['qe']['fee'], 4)}", ""),
        (f"Put · 70d · K={s2['K']:.2f}", money(put["price"], 3), "Bates with jumps · 95% conf.", ""),
        ("12M Euribor in 1 year", pct(s3["expected"], 2), f"Today {pct(s3['current'], 3)} · CIR scenario", "info"),
        ("Heston fit · 15d", money(R_["step1a"]["rmse"], 3), f"RMSE · parity floor {money(R_['data']['15']['floor_mse'], 3)}", ""),
    ]),
    unsafe_allow_html=True,
)

st.markdown("## Live market and model situation")
col_live, col_model = st.columns([1, 1], gap="medium")

with col_live:
    with st.container(border=True):
        st.markdown("#### Market")
        c1, c2 = st.columns([2, 1])
        ticker = c1.text_input("Ticker", value="SM", max_chars=12, key="home_ticker").strip().upper() or "SM"
        refresh = c2.number_input("Refresh (s)", min_value=30, max_value=3600, value=60, step=30, key="home_refresh")

        @st.fragment(run_every=refresh)
        def live_strip(sym: str):
            with guard("Live market data"):
                snap = ld.market_snapshot(sym)
                k1, k2, k3 = st.columns(3)
                k1.metric(f"{sym} spot", money(snap["spot"], 2) if snap["spot"] else DASH,
                          f"{snap['change_pct']:+.2f}% d/d" if snap["change_pct"] is not None else None)
                k2.metric("VIX", num(snap["vix"], 2) if snap["vix"] else DASH, "Volatility index")
                k3.metric("US 10Y", num(snap["tnx"], 2) if snap["tnx"] else DASH, "Yield index")
                ss["home_live"] = snap
                footnote(f"Source: Yahoo Finance via yfinance · snapshot {str(snap['timestamp'])[:19].replace('T', ' ')} UTC. "
                         "Delayed where applicable.")

        live_strip(ticker)
        st.markdown(
            callout(
                "Live market data is indicative only and is never fed into the calibrated model automatically — "
                "the assignment results use the supplied quote file so every number is reproducible.",
                "info",
            ),
            unsafe_allow_html=True,
        )

with col_model:
    with st.container(border=True):
        st.markdown("#### Model")
        p = model_params()
        c1, c2, c3 = st.columns(3)
        spot = c1.number_input("Spot", 1.0, 5000.0, float(S_DEMO), step=1.0, key="home_spot")
        days = c2.number_input("Horizon (days)", 1, 250, 20, key="home_days")
        rate = c3.number_input("Risk-free", -0.05, 0.25, 0.0150, format="%.4f", key="home_rate")
        T = days / 250
        with guard("Scenario pricing"):
            vanilla = float(model_price(spot, spot, T, rate, 0.0, p, "C")[0])
            asian, se, ci = asian_call_qe(spot, spot, T, rate, 0.0, p, int(days), mc_paths(60_000, int(days)))
            saving = 1 - asian / vanilla if vanilla else float("nan")
            k1, k2 = st.columns(2)
            k1.metric("ATM Asian call", money(asian, 4), f"±{1.96 * se:.3f} (95%)")
            k2.metric("ATM vanilla call", money(vanilla, 4), f"Asian {saving:.0%} cheaper")
            ss["last"] = dict(spot=spot, days=days, rate=rate, vanilla=vanilla, asian=asian, client=asian * (1 + FEE))
        footnote("Heston parameters from the 15-day calibration: "
                 + ", ".join(f"{n}={v:.4g}" for n, v in zip(PN, p)) + ".")

st.markdown("## Deliverables")
d1, d2, d3, d4 = st.columns(4, gap="small")
cards = [
    (d1, "📝", "Assignment Tasks", "Every question of Steps 1–3 with charts, validation and plain-language answers.", "pages/2_Assignment_Tasks.py"),
    (d2, "📄", "Report & Downloads", "Answers-only PDF, executable notebook, HTML export and the audit log.", "pages/8_Research_Report.py"),
    (d3, "📈", "Pricing Workbench", "Edit parameters or calibrate on your own quotes, then price any structure.", "pages/1_Live_Simulation.py"),
    (d4, "🔍", "Model Diagnostics", "Residuals, sensitivities, characteristic function and implied-vol surface.", "pages/3_Model_Diagnostics.py"),
]
for col, icon, title, text, path in cards:
    with col:
        with st.container(border=True):
            st.markdown(f"##### {icon} {title}")
            st.markdown(f"<div class='gsq-cap'>{esc(text)}</div>", unsafe_allow_html=True)
            plink(path, "Open", icon="→")

st.markdown(
    callout(
        "**Data caveat.** The supplied quotes violate put–call parity (largest gap "
        f"{money(R_['data']['15']['max_violation'], 2)} at 15 days, {money(R_['data']['60']['max_violation'], 2)} at 60 days), "
        f"which puts an irreducible MSE floor of {R_['data']['15']['floor_mse']:.3f} and {R_['data']['60']['floor_mse']:.3f} on any "
        "arbitrage-free model. Fits are judged against those floors, not against zero.",
        "warn", "Read this first",
    ),
    unsafe_allow_html=True,
)

st.divider()
st.markdown(callout(DISCLAIMER, "danger"), unsafe_allow_html=True)
ai_panel("Dashboard", {"last": ss.get("last")}, [
    "Summarise today's dashboard in three sentences for a non-technical reader",
    "What are the three biggest model risks visible here?",
    "How does the live market compare with the calibration snapshot?",
])
