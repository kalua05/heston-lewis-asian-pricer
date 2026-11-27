import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import *
from utils.theme import badge, callout, kpi_row, page_header

setup("Roadmap", "🧭")

st.markdown(
    page_header(
        "Roadmap",
        "What is already done, what would move the project forward most, and what could be simplified. "
        "Priorities are sized by impact against effort, in the order a reviewer would tackle them.",
        kicker="Reference",
        meta=[badge("Impact vs effort", "info"), badge("Reviewed 2026-11", "neutral")],
    ),
    unsafe_allow_html=True,
)

TONEMAP = {"High": "accent", "Medium": "info", "Low": "neutral"}

ADD = [
    ("Deploy the live app", "High", "Low", "streamlit.app",
     "The brief asks for a live application. Push the repo to GitHub, point Streamlit Community Cloud at app.py, "
     "done — the deployment guide has the exact steps for Cloud, Docker and Render."),
    ("Calibrate on cleaned quotes", "High", "Low", "quant",
     "Fit only to out-of-the-money contracts (calls above spot, puts below) so the parity violations stop polluting "
     "the fit. Report the cleaner MSE beside the raw one."),
    ("Parameter uncertainty bands", "High", "Medium", "quant",
     "Bootstrap the quotes and re-calibrate from many seeds, then show the resulting distribution of κ, θ, σ and ρ. "
     "This turns the 'weak identification' caveat into evidence."),
    ("Control variate for the Asian", "Medium", "Medium", "quant",
     "The geometric Asian option has a closed form. Using it as a control variate cuts Monte Carlo error several-fold "
     "at the same path count."),
    ("Asian Greeks", "Medium", "Medium", "quant",
     "Delta and vega of the Asian call by pathwise differentiation or bump-and-reprice, displayed next to the price."),
    ("Stochastic-rate Heston", "Medium", "High", "quant",
     "Drive the discount rate with the calibrated CIR paths inside the Monte Carlo. The natural bridge between "
     "Step 2 and Step 3, and a research project in its own right."),
    ("Expiry calendar and term structure", "Medium", "Medium", "product",
     "Calibrate each maturity separately and interpolate parameters in T, then expose a term-structure tab."),
    ("Continuous integration", "Low", "Low", "eng",
     "A GitHub Actions workflow running the test suite on every push, so the deployed app cannot break silently."),
]

DONE = [
    ("Single source of truth for numbers", "The pipeline writes one JSON file that feeds the app, the notebook, the "
     "report and the deck. No page contains a hard-coded result."),
    ("Dependency and security hygiene", "Bounded requirements, pinned Python, non-root container, no secrets in the "
     "repo, pip-audit and bandit reviewed."),
    ("Design system", "One tokens file drives colours, spacing, components and the Plotly template, so every page "
     "looks like part of the same product."),
    ("States and validation", "Every page handles loading, empty and error states; every input is bounded; uploads "
     "are schema-validated."),
    ("Tests", "Regression suite covering the Fourier engines, the Monte Carlo schemes, calibration, CIR and the "
     "security helpers, plus a smoke test of every page."),
]

REMOVE = [
    ("Separate Presentation page", "Keep it — it now rebuilds the deck from the results file and doubles as the "
     "speaker script. Cost of keeping it is near zero.", "Kept"),
    ("Real-Time Data page", "Kept as an explicit demo with graceful degradation; nothing graded depends on it.", "Kept"),
    ("Four near-empty info pages", "About Developer, Contact, Documentation and Disclaimer were merged into one "
     "About & Docs page with tabs.", "Merged"),
    ("AI panels on every page", "Now a single collapsible assistant, hidden automatically when no API key is set, "
     "instead of a button and a text box on each page.", "Consolidated"),
]

t1, t2, t3 = st.tabs(["➕ Backlog", "✅ Done", "🧹 Simplified"])

with t1:
    st.markdown(kpi_row([
        ("High impact", str(sum(1 for a in ADD if a[1] == "High")), "do these first", "accent"),
        ("Medium", str(sum(1 for a in ADD if a[1] == "Medium")), "next cycle", "info"),
        ("Low", str(sum(1 for a in ADD if a[1] == "Low")), "nice to have", ""),
        ("Total items", str(len(ADD)), "open", ""),
    ]), unsafe_allow_html=True)

    flt = st.segmented_control("Impact", ["All", "High", "Medium", "Low"], default="All", key="rm_flt") or "All"
    items = [a for a in ADD if flt == "All" or a[1] == flt]
    for i in range(0, len(items), 2):
        cols = st.columns(2, gap="medium")
        for col, (title, impact, effort, kind, desc) in zip(cols, items[i:i + 2]):
            with col:
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.markdown(badge(f"Impact {impact}", TONEMAP[impact]) + " " + badge(f"Effort {effort}", "neutral"),
                                unsafe_allow_html=True)
                    st.markdown(f"<div class='gsq-cap' style='margin-top:.5rem'>{esc(desc)}</div>",
                                unsafe_allow_html=True)

with t2:
    for title, desc in DONE:
        with st.container(border=True):
            st.markdown(f"**✅ {title}**")
            st.markdown(f"<div class='gsq-cap'>{esc(desc)}</div>", unsafe_allow_html=True)

with t3:
    st.markdown(caption("Nothing graded was deleted. These are the simplifications that make the app shorter without "
                        "losing a single result."), unsafe_allow_html=True)
    for title, desc, action in REMOVE:
        with st.container(border=True):
            c = st.columns([3, 1])
            c[0].markdown(f"**{title}**")
            c[1].markdown(badge(action, "ok" if action == "Kept" else "info"), unsafe_allow_html=True)
            st.markdown(f"<div class='gsq-cap'>{esc(desc)}</div>", unsafe_allow_html=True)

st.markdown(
    callout("<b>Suggested order.</b> Deploy first — a live link is worth more than any additional feature. Then clean "
            "the calibration data, because it addresses the single biggest weakness in the results. Everything else is "
            "polish.", "info", "If you only do one thing"),
    unsafe_allow_html=True,
)
