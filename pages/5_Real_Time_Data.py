import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import *
from utils.theme import badge, callout, empty_state, page_header

setup("Market Data", "📡")

st.markdown(
    page_header(
        "Market data",
        "Live snapshot, listed option chain and headlines for SM Energy. Data are delayed, cached and "
        "degrade gracefully: if the provider is unavailable the page says so instead of inventing numbers.",
        kicker="Overview",
        meta=[badge("Yahoo Finance", "info"), badge("Cached 60 s", "neutral"), badge("Indicative only", "warn")],
    ),
    unsafe_allow_html=True,
)

c = st.columns([1, 1, 2])
ticker = c[0].text_input("Ticker", value="SM", max_chars=12, key="rt_ticker").strip().upper() or "SM"
refresh = c[1].number_input("Refresh (s)", min_value=30, max_value=3600, value=60, step=30, key="rt_refresh")
auto = c[2].toggle("Auto-refresh", value=False, key="rt_live",
                   help="Off by default to avoid hammering the free data provider.")


@st.fragment(run_every=refresh if auto else None)
def dashboard(sym: str):
    with guard("Market snapshot"):
        snap = ld.market_snapshot(sym)
        if not snap or snap.get("spot") is None:
            st.markdown(empty_state("No quote returned",
                                    f"The provider did not return a price for {sym}.",
                                    "Check the ticker symbol, or use the assignment dataset instead."),
                        unsafe_allow_html=True)
            return
        st.markdown(
            kpi_row([
                (f"{sym} last", money(snap["spot"], 2), describe_change(snap["change_pct"]) if snap["change_pct"] is not None else "session change", "accent"),
                ("S&P 500", num(snap["spx"], 2), "Benchmark", ""),
                ("VIX", num(snap["vix"], 2), "30-day implied vol", ""),
                ("US 10Y", num(snap["tnx"], 2), "Yield index", ""),
            ]),
            unsafe_allow_html=True,
        )
        footnote(f"Snapshot {str(snap['timestamp'])[:19].replace('T', ' ')} UTC · source Yahoo Finance via yfinance. "
                 "Delayed where applicable; not a tradable quote.")
        ss["home_live"] = snap

    st.markdown("## Option chain")
    with guard("Option chain"):
        exps = ld.expiries(sym)
        if not exps:
            st.markdown(empty_state("No listed expiries", f"The provider returned no option expiries for {sym}.",
                                    "Illiquid or non-optionable tickers behave this way."), unsafe_allow_html=True)
        else:
            expiry = st.selectbox("Expiry", exps, key="rt_exp")
            chain = ld.chain(expiry, sym)
            if chain is None or chain.empty:
                st.markdown(empty_state("Empty chain", "No two-sided quotes at that expiry.",
                                        "Try another expiry or a more liquid ticker."), unsafe_allow_html=True)
            else:
                cc = st.columns(2)
                cc[0].metric("Contracts", f"{len(chain):,}")
                cc[1].metric("Strikes", f"{chain['Strike'].nunique()}")
                st.dataframe(chain.sort_values(["Type", "Strike"]).round(4), hide_index=True, width="stretch",
                             column_config={"impliedVolatility": st.column_config.NumberColumn("IV", format="%.1f%%")})
                st.download_button("⬇ CSV", chain.to_csv(index=False).encode(), f"{sym}_{expiry}_chain.csv",
                                   "text/csv", key="rt_dl")

    st.markdown("## Headlines")
    with guard("Headlines"):
        items = ld.news(sym)
        if not items:
            st.markdown(empty_state("No headlines", "The news feed returned nothing for this ticker."), unsafe_allow_html=True)
        else:
            for n in items:
                st.markdown(f"- **{esc(n['title'])}** — <span class='gsq-cap'>{esc(n['publisher'])}</span>",
                            unsafe_allow_html=True)
            footnote("Headlines are untrusted third-party text and are never executed or interpreted as instructions.")


dashboard(ticker)

st.divider()
st.markdown(
    callout("Yahoo Finance rate-limits anonymous callers. If the page shows a fallback state, wait a minute and "
            "retry, or rely on the supplied assignment data — no graded result depends on this page.", "info"),
    unsafe_allow_html=True,
)
ai_panel("Market Data", {"live": ss.get("home_live")}, [
    "Interpret this market snapshot for an equity derivatives desk",
    "How should an investor read VIX at this level?",
    "What risks affect the SM option model today?",
])
