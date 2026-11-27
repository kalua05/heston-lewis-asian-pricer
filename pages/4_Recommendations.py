import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import *
from utils.theme import badge, callout, empty_state, kpi_row, page_header

setup("Recommendations", "💡")

st.markdown(
    page_header(
        "Recommendations",
        "Scenario-based guidance for three audiences, generated from the calibrated model rather than from a "
        "view on the stock. Every statement is illustrative and carries its own caveat.",
        kicker="Analysis",
        meta=[badge("Not investment advice", "danger"), badge("Model-driven", "info")],
    ),
    unsafe_allow_html=True,
)

ensure()
p = tuple(ss.p)
r = ss.res

with guard("Recommendation engine"):
    T20 = 20 / 250
    v = float(lewis_call(S_DEMO, S_DEMO, T20, R_DEMO, 0.0, p)[0])
    a, se, ci = asian_call_qe(S_DEMO, S_DEMO, T20, R_DEMO, 0.0, p, 20, 100_000)

st.markdown(
    kpi_row([
        ("Asian call (ATM, 20d)", money(a, 4), f"95% CI {delta_span(*ci, 3)}", "accent"),
        ("Vanilla call (ATM, 20d)", money(v, 4), "Lewis / Fourier", ""),
        ("Asian discount", pct(1 - a / v if v else float("nan"), 1), "vs the vanilla", "info"),
        ("Client price", money(a * (1 + FEE), 4), "Fair value + 4% fee", ""),
    ]),
    unsafe_allow_html=True,
)

st.markdown(callout(DISCLAIMER, "danger"), unsafe_allow_html=True)

audience = st.segmented_control("Audience", ["Retail investor", "Professional investor", "Corporate treasury"],
                                default="Professional investor", key="rec_aud") or "Professional investor"

st.markdown(f"## Guidance for a {audience.lower()}")
with guard("Guidance"):
    lines = recommendations(S_DEMO, S_DEMO, T20, v, a, ci, r["rmse"], r["feller"], p)
    for line in lines:
        st.markdown(f"- {line}")

checklists = {
    "Retail investor": [
        "Compare the premium with the downside protection you actually need; the Asian caps the upside.",
        "Size the position so a total loss is tolerable, and write down the exit condition before entering.",
        "Prefer the simpler vanilla if a path-dependent average payoff is hard to explain to yourself.",
        "Check liquidity and the bid–ask spread — model value is not a tradable price.",
    ],
    "Professional investor": [
        "Stress spot, vol-of-vol, correlation and jump intensity separately; the surface is a fit, not a forecast.",
        "Compare Heston and Bates outputs rather than trusting one point estimate.",
        "Hold delta/vega hedges with listed strikes near the money and re-calibrate daily.",
        "Carry a model-risk reserve quantified by the spread across calibrations (see Model Diagnostics).",
    ],
    "Corporate treasury": [
        "Align the notional with the actual cash-flow or commodity exposure, not with a directional view.",
        "Evaluate counterparty risk, collateral terms and accounting treatment before execution.",
        "Test the hedge under a rate scenario from Step 3b as well as a spot scenario.",
        "Document the model, its assumptions, and the approval trail for audit.",
    ],
}
c = st.columns([1.1, 1], gap="medium")
with c[0]:
    with st.container(border=True):
        st.markdown("#### Checklist")
        for item in checklists[audience]:
            st.markdown(f"- {item}")
with c[1]:
    with st.container(border=True):
        st.markdown("#### What would invalidate this")
        st.markdown(
            "- A structural break in SM Energy's volatility regime (earnings, OPEC decisions, gas prices).\n"
            "- Put–call parity violations being resolved in the market — the fit would move materially.\n"
            "- Liquidity drying up in the listed strikes used to hedge.\n"
            "- A rate move far outside the CIR 95% band from Step 3b."
        )

st.markdown("## Relative value: rich / cheap against the model")
d = rich_cheap(ss.df, r["model"], S_DEMO, ss.T, R_DEMO, 0.0)
counts = d["Signal"].value_counts()
c = st.columns(3)
for col, label, key in zip(c, ["Rich vs model", "Cheap vs model", "Fair"], ["Rich vs model (sell-side candidate)",
                                                                          "Cheap vs model (buy-side candidate)", "Fair"]):
    col.metric(label, int(counts.get(key, 0)), "quotes at 15 days")

st.dataframe(
    d[["Strike", "Type", "Price", "Model", "Resid", "MktIV", "ModIV", "Signal"]].round(5),
    hide_index=True, width="stretch",
    column_config={"MktIV": st.column_config.NumberColumn("Mkt IV", format="%.2f%%"),
                   "ModIV": st.column_config.NumberColumn("Model IV", format="%.2f%%")},
)
export_row(d, "relative_value_15d", "rec_export")

st.markdown(
    callout("A “rich/cheap” label is a <b>model residual</b>, not an arbitrage. With ten quotes that violate "
            "put–call parity, a residual of a few cents is inside the noise of the calibration itself.",
            "warn", "How to read the signals"),
    unsafe_allow_html=True,
)

ai_panel("Recommendations", {"audience": audience, "live": ss.get("home_live")}, [
    "Write a short recommendation for this audience",
    "What would invalidate this recommendation?",
    "Build a downside / base / upside scenario checklist",
])
