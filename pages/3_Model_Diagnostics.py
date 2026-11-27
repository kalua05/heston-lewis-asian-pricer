import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import *
from utils.theme import badge, callout, kpi_row, page_header

setup("Model Diagnostics", "🔍")

st.markdown(
    page_header(
        "Model diagnostics",
        "Where the calibrated model fits, where it does not, and why. Residuals, parameter sensitivities, "
        "the Lewis integrand and characteristic function, and the implied-volatility surface.",
        kicker="Analysis",
        meta=[badge("15-day calibration", "accent"), badge("Lewis integrand", "info"), badge("Finite-difference sensitivities", "info")],
    ),
    unsafe_allow_html=True,
)

ensure()
df, res, T, p = ss.df, ss.res, ss.T, tuple(ss.p)

st.markdown(
    kpi_row([
        ("RMSE", money(res["rmse"], 4), "Price units", "accent"),
        ("MSE", f"{res['mse']:.5f}", "Plain mean squared error", ""),
        ("Feller margin", f"{res['feller']:+.4f}", "2κθ − σ² ≥ 0 holds" if res["feller"] >= 0 else "Violated — QE scheme", ""),
        ("Bounds hit", str(len(res["at_bounds"])), ", ".join(res["at_bounds"]) if res["at_bounds"] else "None", "warn" if res["at_bounds"] else ""),
    ]),
    unsafe_allow_html=True,
)

if res.get("at_bounds"):
    st.markdown(
        callout("Some parameters sit on an optimiser bound. That is a statement about the <b>data</b>, not the "
                "optimiser: with ten noisy quotes several parameter pairs fit equally well. Judge the model by prices "
                "and by out-of-sample stability, never by a single parameter value.", "warn", "Identification"),
        unsafe_allow_html=True,
    )

d = rich_cheap(df, res["model"], S_DEMO, T, R_DEMO, 0.0)
tab_fit, tab_sens, tab_engine, tab_surface, tab_whatif = st.tabs(
    ["Fit quality", "Parameter sensitivity", "Engine internals", "Volatility surface", "What-if & regimes"]
)

# ------------------------------------------------------------------ fit quality
with tab_fit:
    c = st.columns(2, gap="medium")
    with c[0]:
        mk, md_ = np.array(df["Price"]), np.array(res["model"])
        f = go.Figure()
        f.add_trace(go.Scatter(x=df["Strike"], y=mk, mode="markers", name="Market",
                               marker=dict(size=9, line=dict(width=1, color="rgba(255,255,255,.35)"))))
        f.add_trace(go.Scatter(x=df["Strike"], y=md_, mode="lines+markers", name="Model",
                               line=dict(dash="dot", width=2), marker=dict(symbol="x", size=8)))
        f.update_layout(title="Market vs model price", xaxis_title="Strike ($)", yaxis_title="Price ($)", height=340)
        chart(f)
    with c[1]:
        g = go.Figure()
        g.add_trace(go.Scatter(x=df["Strike"], y=np.array(d["MktIV"], float) * 100, mode="markers", name="Market IV"))
        g.add_trace(go.Scatter(x=df["Strike"], y=np.array(d["ModIV"], float) * 100, mode="markers",
                               name="Model IV", marker=dict(symbol="x")))
        g.update_layout(title="Implied volatility", xaxis_title="Strike ($)", yaxis_title="IV (%)", height=340)
        chart(g)

    c = st.columns(2, gap="medium")
    with c[0]:
        h = go.Figure(go.Bar(x=[f"{k:g}{t}" for k, t in zip(df["Strike"], df["Type"])],
                             y=np.array(res["model"]) - np.array(df["Price"]),
                             marker_color=[ACCENT if t == "C" else "#F87171" for t in df["Type"]]))
        h.update_layout(title="Pricing error (model − market)", xaxis_title="Strike and type", yaxis_title="$", height=340)
        chart(h)
    with c[1]:
        wide = d.pivot_table(index="Strike", columns="Type", values="Resid")
        if {"C", "P"}.issubset(set(wide.columns)):
            corr = wide[["C", "P"]].corr().iloc[0, 1]
            st.markdown(f"**Call/put residual correlation: {corr:+.3f}**")
            st.markdown(
                callout("Residuals that move together across calls and puts mean the misfit is a "
                        "<b>level/skew</b> effect, not independent noise: the quotes themselves are mutually "
                        "inconsistent (put–call parity), so no arbitrage-free model can fit both sides.",
                        "info", "How to read this"),
                unsafe_allow_html=True,
            )
        st.markdown("##### Residual heatmap")
        heat = go.Figure(go.Heatmap(z=wide.T.values, x=[f"{s:g}" for s in wide.index], y=list(wide.columns),
                                    colorscale="RdBu_r", zmid=0, colorbar=dict(title="$")))
        heat.update_layout(height=250, xaxis_title="Strike", yaxis_title="Type", margin=dict(l=40, r=10, t=20, b=40))
        chart(heat)

    st.markdown("##### Rich / cheap relative to the model")
    st.dataframe(
        d[["Strike", "Type", "Price", "Model", "Resid", "MktIV", "ModIV", "Signal"]].round(5),
        hide_index=True, width="stretch",
        column_config={
            "MktIV": st.column_config.NumberColumn("Mkt IV", format="%.2f%%"),
            "ModIV": st.column_config.NumberColumn("Model IV", format="%.2f%%"),
        },
    )
    export_row(d, "diagnostics_rich_cheap", "diag_export")

# ------------------------------------------------------------------ sensitivities
with tab_sens:
    st.markdown("Bump-and-reprice sensitivity of the at-the-money 20-day call to each parameter (1% relative bump).")
    base = float(lewis_call(S_DEMO, S_DEMO, T, R_DEMO, 0.0, p)[0])
    rows = []
    for i, nm in enumerate(PN):
        q_ = list(p)
        q_[i] = q_[i] * 1.01 if q_[i] else 0.001
        bumped = float(lewis_call(S_DEMO, S_DEMO, T, R_DEMO, 0.0, tuple(q_))[0])
        rows.append({"parameter": nm, "value": p[i], "price": bumped,
                     "dPrice/dparam": (bumped - base) / ((abs(p[i]) * 0.01) or 0.001)})
    sens = pd.DataFrame(rows)
    sens["abs"] = sens["dPrice/dparam"].abs()
    sens = sens.sort_values("abs", ascending=False).drop(columns="abs")
    c = st.columns([1, 1.3], gap="medium")
    with c[0]:
        st.dataframe(sens.round(5), hide_index=True, width="stretch")
    with c[1]:
        f = go.Figure(go.Bar(x=sens["parameter"], y=sens["dPrice/dparam"], marker_color=ACCENT))
        f.update_layout(title="Parameter ranking (ATM call)", xaxis_title="Parameter", yaxis_title="$ per unit", height=320)
        chart(f)
    st.markdown(
        callout("Ranking is dominated by v₀ and σ (level and curvature of the smile). κ and θ barely move a "
                "20-day price, which is exactly why they are weakly identified at that maturity.", "info", "Interpretation"),
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------------ engine internals
with tab_engine:
    from utils.heston import heston_cf

    c = st.columns(2, gap="medium")
    with c[0]:
        u, f_ = integrand(S_DEMO, S_DEMO, T, R_DEMO, 0.0, p)
        fig = go.Figure(go.Scatter(x=u[:900], y=f_[:900], line=dict(color=ACCENT)))
        fig.update_layout(title="Lewis integrand (ATM, ν = ½)", xaxis_title="u", yaxis_title="Integrand", height=330)
        chart(fig)
    with c[1]:
        uu = np.linspace(1e-8, 40, 900)
        cf = heston_cf(uu, T, *p)
        fig = go.Figure([
            go.Scatter(x=uu, y=cf.real, name="Re φ"),
            go.Scatter(x=uu, y=cf.imag, name="Im φ"),
        ])
        fig.update_layout(title="Heston characteristic function", xaxis_title="u", yaxis_title="φ(u)", height=330)
        chart(fig)

    st.markdown("##### Quadrature check")
    from utils.lewis import U_MAX, PANEL, ORDER
    st.markdown(
        f"Grid in use: <b>{ORDER}</b>-point Gauss–Legendre panels of width <b>{PANEL}</b> out to "
        f"U<sub>max</sub> = <b>{U_MAX:.0f}</b>. The regression suite compares both transforms with adaptive "
        f"quadrature on a 5e-3 tolerance, which is where the “worst error $0.004” figure in the audit log comes from.",
        unsafe_allow_html=True,
    )
    st.markdown(
        "The integral uses composite Gauss–Legendre quadrature (16-point panels of width 5 up to "
        "U<sub>max</sub> = 400). Widening or narrowing the panel changes prices by less than $0.001 on these "
        "quotes, and the regression suite compares both engines with adaptive quadrature at a 5e-3 tolerance.",
        unsafe_allow_html=True,
    )
    st.markdown(
        callout("<b>Why Fourier?</b> The Heston density has no closed form, but its characteristic function does. "
                "One smooth integral replaces a nested inversion, which makes calibration (thousands of price "
                "evaluations) cheap enough to run inside a web request.", "info"),
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------------ surface
with tab_surface:
    Ks = np.linspace(0.9 * S_DEMO, 1.08 * S_DEMO, 17)
    Ts = [10, 20, 40, 60, 90, 120]
    Z = np.array([[implied_vol(float(lewis_call(S_DEMO, k, t / 250, R_DEMO, 0.0, p)[0]), S_DEMO, k, t / 250,
                               R_DEMO, 0.0, "C") * 100 for k in Ks] for t in Ts])
    surf = go.Figure(go.Surface(x=Ks, y=Ts, z=Z, colorscale="Teal"))
    surf.update_layout(title="Model-implied volatility surface", height=520,
                       scene=dict(xaxis_title="Strike ($)", yaxis_title="Days", zaxis_title="IV (%)"))
    chart(surf)
    st.markdown(
        callout("Quotes exist only at 15, 60 and 120 days. Everything between and beyond is the model's "
                "extrapolation — useful for intuition, never a tradable mark.", "warn", "Extrapolation"),
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------------ what-if
with tab_whatif:
    c = st.columns(3)
    sp = c[0].slider("Spot", 0.75 * S_DEMO, 1.25 * S_DEMO, S_DEMO, step=1.0)
    kk = c[1].slider("Strike", 0.75 * S_DEMO, 1.25 * S_DEMO, S_DEMO, step=1.0)
    dd = c[2].slider("Days", 5, 120, 20)
    with guard("What-if"):
        px_val = float(lewis_call(sp, kk, dd / 250, R_DEMO, 0.0, p)[0])
        st.markdown(kpi_row([("What-if call", money(px_val, 4), f"S {sp:.1f} · K {kk:.1f} · {dd}d", "accent")]),
                    unsafe_allow_html=True)
        grid = np.linspace(0.8 * S_DEMO, 1.2 * S_DEMO, 60)
        f = go.Figure(go.Scatter(x=grid, y=[float(lewis_call(s, kk, dd / 250, R_DEMO, 0.0, p)[0]) for s in grid],
                                 line=dict(color=ACCENT, width=2)))
        f.add_vline(x=sp, line_dash="dot", line_color="#8194AC")
        f.update_layout(title="Price vs spot", xaxis_title="Spot ($)", yaxis_title="Call ($)", height=320)
        chart(f)

    st.markdown("##### Scenario regimes")
    regimes = {
        "Calm": (0.03, 2.0, 0.03, 0.30, -0.50),
        "Calibrated": p,
        "Stressed": (0.12, 1.0, 0.10, 0.80, -0.80),
    }
    rows = []
    with guard("Scenario engine"):
        for nm, pp in regimes.items():
            rows.append({"Regime": nm,
                         "Vanilla ATM 20d": float(lewis_call(S_DEMO, S_DEMO, 20 / 250, R_DEMO, 0.0, pp)[0]),
                         "Asian ATM 20d": asian_call_qe(S_DEMO, S_DEMO, 20 / 250, R_DEMO, 0.0, pp, 20, 40_000)[0]})
    st.dataframe(pd.DataFrame(rows).round(4), hide_index=True, width="stretch")
    footnote("Calm and stressed sets are illustrative parameter choices, not calibrated results.")

ai_panel("Model Diagnostics", {"rmse": res["rmse"], "at_bounds": res["at_bounds"]}, [
    "What does the residual heatmap tell me?",
    "Explain the Lewis integrand plot simply",
    "Compare the calm and stressed regimes",
])
