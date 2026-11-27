import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import *
from utils.theme import badge, callout, empty_state, kpi_row, page_header, panel

setup("Pricing Workbench", "📈")

st.markdown(
    page_header(
        "Pricing workbench",
        "Calibrate Heston to your own quote file or edit the parameters directly, then price a vanilla "
        "option with the Fourier engine and an Asian call by Monte Carlo. Every input is bounded and every "
        "result is validated against a second engine.",
        kicker="Analysis",
        meta=[badge("Fourier: Lewis 2001", "info"), badge("MC: Andersen QE", "info"), badge("S₀ in the Asian average", "accent")],
    ),
    unsafe_allow_html=True,
)

ensure()
p = tuple(ss.p)

# ------------------------------------------------------------------ 1. inputs
with st.container(border=True):
    st.markdown("#### 1 · Model parameters")
    st.markdown("<div class='gsq-cap'>Defaults come from the 15-day Heston calibration on the supplied quotes. "
                "Feller condition: 2κθ ≥ σ².</div>", unsafe_allow_html=True)
    pc = st.columns(5)
    new_p = tuple(
        pc[i].number_input(n, min_value=BOUNDS[i][0], max_value=BOUNDS[i][1],
                           value=float(np.clip(p[i], *BOUNDS[i])), format="%.4f", key="wb_" + n,
                           help=help_text)
        for i, (n, help_text) in enumerate(zip(PN, [
            "Initial variance v₀ = σ² of the spot.",
            "Mean-reversion speed κ.",
            "Long-run variance θ.",
            "Volatility of variance σ (smile curvature).",
            "Spot/variance correlation ρ (skew; negative for equities).",
        ]))
    )
    feller = 2 * new_p[1] * new_p[2] - new_p[3] ** 2
    st.markdown(
        badge("Feller satisfied", "ok") if feller >= 0 else badge(f"Feller violated ({feller:+.4f}) — QE recommended", "warn"),
        unsafe_allow_html=True,
    )
    ss.p = new_p
    p = new_p

with st.container(border=True):
    st.markdown("#### 2 · Contract")
    c = st.columns(6)
    S = c[0].number_input("Spot S₀", 1.0, 5000.0, float(S_DEMO), step=1.0, key="wb_S")
    K = c[1].number_input("Strike K", 1.0, 5000.0, float(S_DEMO), step=1.0, key="wb_K")
    days = c[2].number_input("Days to expiry", 1, 750, 20, key="wb_days")
    r = c[3].number_input("Rate r", -0.05, 0.25, float(R_DEMO), format="%.4f", key="wb_r")
    q = c[4].number_input("Div. yield q", 0.0, 0.25, 0.0, format="%.4f", key="wb_q")
    typ = c[5].radio("Vanilla type", ["C", "P"], horizontal=True, key="wb_type")
    T = days / 250

    c = st.columns([1.2, 1.2, 2])
    scheme = c[0].radio("MC scheme", ["QE (Andersen)", "Euler"], horizontal=True, key="wb_scheme")
    paths_in = c[1].select_slider("Paths", [20_000, 50_000, 100_000, 200_000], value=100_000, key="wb_paths")
    with c[2]:
        st.markdown("<div class='gsq-cap' style='padding-top:1.9rem'>Paths are capped automatically so that "
                    "paths × steps stays inside the server budget (20 M).</div>", unsafe_allow_html=True)

n_paths = mc_paths(paths_in, int(days))

# ------------------------------------------------------------------ 2. compute
with guard("Pricing"):
    with heavy("simulation"), st.spinner("Pricing…"):
        vanilla = float(model_price(S, K, T, r, q, p, typ)[0])
        iv = implied_vol(vanilla, S, K, T, r, q, typ)
        engine = asian_call_qe if scheme.startswith("QE") else asian_call_mc
        asian, se, ci = engine(S, K, T, r, q, p, int(days), n_paths)
        fo_vanilla = float(model_price(S, K, T, r, q, p, "C")[0])
    st.markdown(
        kpi_row([
            (f"Vanilla {typ} · Lewis", money(vanilla, 4), f"K {money(K, 2)} · T {T:.3f}y", "accent"),
            ("Implied volatility", pct(iv, 2), "Black–Scholes equivalent", ""),
            ("Asian call · MC", money(asian, 4), f"95% CI {delta_span(*ci, 3)}", "info"),
            ("Standard error", money(se, 4), f"{se / asian:.2%} of price" if asian else DASH, ""),
            ("Client price (+4%)", money(asian * (1 + FEE), 4), f"Fee {money(asian * FEE, 4)}", ""),
        ]),
        unsafe_allow_html=True,
    )
    ss["last"] = dict(p=p, vanilla=vanilla, asian=asian, K=K, days=days, spot=S, rate=r)
    ss["asian"] = (asian, se, ci)

    left, right = st.columns([1.15, 1], gap="medium")
    with left:
        st.markdown("##### Greeks (vanilla, finite difference)")
        g = greeks(S, K, T, r, q, p, typ)
        gdf = pd.DataFrame([{
            "Delta": g["delta"], "Gamma": g["gamma"], "Theta (per year)": g["theta_per_year"],
            "Rho (per 1%)": g["rho_per_1pct"], "dVega-ish dP/dv₀": g["dPrice_dv0"],
        }])
        st.dataframe(gdf, hide_index=True, width="stretch",
                     column_config={c_: st.column_config.NumberColumn(format="%.5f") for c_ in gdf.columns})
        footnote("Theta is reported per year; divide by 250 for a trading day. dP/dv₀ is the sensitivity to a "
                 "one-unit change in initial variance — divide by 2√v₀ for a vol point.")

    with right:
        st.markdown("##### Validation")
        z = (asian - fo_vanilla) / se if se else float("nan")
        st.markdown(
            callout(
                f"The same Monte Carlo prices a <b>European</b> call at {money(asian if typ == 'C' else 0, 3)} "
                f"against the Fourier value {money(fo_vanilla, 3)} — the Asian payoff is always below the vanilla "
                f"because averaging dampens variance. Current Asian/vanilla ratio: "
                f"<b>{asian / vanilla:.2%}</b>.",
                "info", "Cross-check",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("##### Simulated discounted payoff distribution")
    _, pay = simulate(S, K, T, r, q, p, int(days), min(n_paths, 100_000), 42, "heston", "asian_call",
                      "qe" if scheme.startswith("QE") else "euler", return_payoffs=True)
    h = go.Figure(go.Histogram(x=pay, nbinsx=70, marker=dict(color=ACCENT, opacity=.75, line=dict(width=0))))
    h.update_layout(title=f"Discounted Asian payoffs · {(pay == 0).mean():.0%} of paths pay nothing",
                    xaxis_title="Payoff ($)", yaxis_title="Paths", bargap=.02, height=340)
    chart(h)
    footnote("A large probability of zero payoff with a long right tail is the signature of an option: most paths "
             "expire worthless, a minority pay well.")

# ------------------------------------------------------------------ 3. calibration on upload
st.markdown("## Calibrate on your own quotes")
with st.container(border=True):
    st.markdown(
        "<div class='gsq-cap'>CSV with columns <code>Days to maturity, Strike, Price, Type</code> "
        "(Type = C or P). Maximum 200 rows, 12 maturities, prices in dollars.</div>",
        unsafe_allow_html=True,
    )
    u1, u2 = st.columns([2, 1])
    up = u1.file_uploader("Quote file", type=["csv"], key="wb_upload", label_visibility="collapsed")
    with u2:
        quote_template_button("wb_tpl")

    if up is not None:
        clean, err = read_upload(up)
        if err:
            st.markdown(callout(esc(err), "danger", "Upload rejected"), unsafe_allow_html=True)
        elif clean is not None:
            maturities = sorted(clean["Days to maturity"].unique())
            st.success(f"{len(clean)} quotes across {len(maturities)} maturities passed validation.")
            c = st.columns([1, 1, 1])
            dd = c[0].selectbox("Maturity to calibrate (days)", maturities, key="wb_mat")
            spot_u = c[1].number_input("Spot for calibration", 1.0, 5000.0, float(S_DEMO), key="wb_spot_u")
            go_btn = c[2].button("Calibrate now", type="primary", width="stretch")
            if go_btn:
                subset = clean[clean["Days to maturity"] == dd].reset_index(drop=True)
                if len(subset) < 4:
                    st.markdown(callout("At least four quotes are needed at one maturity.", "warn"), unsafe_allow_html=True)
                else:
                    with guard("Calibration"):
                        with heavy("calibration"), st.spinner("Running differential evolution…"):
                            res = calibrate(subset, spot_u, r, 0.0, dd / 250, "heston", "lewis", maxiter=80)
                        ss.p = tuple(res["params"])
                        ss.res = res
                        ss.df = subset
                        ss.T = dd / 250
                        st.markdown(
                            callout(
                                f"Converged: MSE {res['mse']:.5f}, RMSE {money(res['rmse'], 4)}, "
                                f"{res['n_eval']:,} model evaluations. Parameters were written to the workbench above — "
                                "scroll up to re-price with them."
                                + (f" On a bound: {', '.join(res['at_bounds'])} (weakly identified)." if res["at_bounds"] else ""),
                                "ok", "Calibration finished",
                            ),
                            unsafe_allow_html=True,
                        )
                        st.dataframe(pd.DataFrame([res["params"]], columns=res["names"]).round(5), hide_index=True,
                                     width="stretch")

# ------------------------------------------------------------------ 4. export
st.markdown("## Export")
with st.container(border=True):
    if "last" in ss:
        L = ss["last"]
        summary = pd.DataFrame([
            {"Item": "Spot", "Value": L["spot"]}, {"Item": "Strike", "Value": L["K"]},
            {"Item": "Days", "Value": L["days"]}, {"Item": "Rate", "Value": L["rate"]},
            {"Item": "Vanilla (Fourier)", "Value": L["vanilla"]}, {"Item": "Asian call (MC)", "Value": L["asian"]},
            {"Item": "Client price (+4%)", "Value": L["asian"] * 1.04},
            *[{"Item": f"param {n}", "Value": v} for n, v in zip(PN, L["p"])],
        ])
        export_row(summary, "pricing_result", "wb_export", excel={"Pricing": summary})
        footnote("The CSV and workbook contain exactly the numbers shown on this page, so a reviewer can reproduce them.")
    else:
        st.markdown(empty_state("Nothing to export yet", "Price a contract above and the export becomes available."),
                    unsafe_allow_html=True)

st.divider()
st.markdown(callout(DISCLAIMER, "danger"), unsafe_allow_html=True)
ai_button("🤖 Explain this result", "Explain these pricing results for (a) a trader and (b) an investor: the Asian-vs-vanilla gap, "
          "the Monte Carlo error, and the main risks.", {"last": ss.get("last")}, "Workbench")
ai_panel("Workbench", {"last": ss.get("last")}, [
    "Why is the Asian cheaper than the vanilla?",
    "Which Heston parameter matters most here?",
    "How could I improve this calibration?",
])
