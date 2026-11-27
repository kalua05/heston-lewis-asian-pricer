import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import *
from utils.theme import badge, callout, kpi_row, page_header

setup("Assignment Tasks", "📝")

R_ = get_results()
M = R_["meta"]

st.markdown(
    page_header(
        "GWP1 · Steps 1–3",
        f"Every question of the brief, answered from one deterministic pipeline and rendered with the numbers the "
        f"report and the notebook use. Spot ${M['spot']:.2f}, r = {M['r']:.2%}, {M['days_per_year']} trading days/year, "
        f"fee {M['fee']:.0%}, {M['n_mc']:,} Monte Carlo paths.",
        kicker="Assignment",
        meta=[badge(f"Generated {M['generated'][:10]}", "neutral"), badge("Answers only · no code", "info"),
              badge("Reproducible", "ok")],
    ),
    unsafe_allow_html=True,
)


def fit_figs(fit, title):
    K, ty = np.array(fit["strike"]), np.array(fit["type"])
    mk, md_ = np.array(fit["market"]), np.array(fit["model_price"])
    f = go.Figure()
    for t_, c_, nm in (("C", "#60A5FA", "calls"), ("P", "#F87171", "puts")):
        m = ty == t_
        f.add_trace(go.Scatter(x=K[m], y=mk[m], mode="markers", name=f"Market {nm}",
                               marker=dict(color=c_, size=9)))
        f.add_trace(go.Scatter(x=K[m], y=md_[m], mode="lines+markers", name=f"Model {nm}",
                               line=dict(color=c_, dash="dot"), marker=dict(symbol="x", size=8)))
    f.update_layout(title=f"{title} · price fit", xaxis_title="Strike ($)", yaxis_title="Price ($)", height=330)

    g = go.Figure([
        go.Scatter(x=K, y=np.array(fit["mkt_iv"], float) * 100, mode="markers", name="Market IV"),
        go.Scatter(x=K, y=np.array(fit["mod_iv"], float) * 100, mode="markers", name="Model IV",
                   marker=dict(symbol="x")),
    ])
    g.update_layout(title="Implied volatility", xaxis_title="Strike ($)", yaxis_title="IV (%)", height=330)

    h = go.Figure(go.Bar(x=[f"{k:g}{t}" for k, t in zip(K, ty)], y=np.array(fit["resid"]) * -1,
                         marker_color=np.where(ty == "C", "#60A5FA", "#F87171")))
    h.update_layout(title="Pricing error (market − model)", xaxis_title="Strike and type", yaxis_title="$", height=330)

    c = st.columns(3)
    for col, fig in zip(c, (f, g, h)):
        with col:
            chart(fig)


def params_table(fit):
    st.markdown(
        kpi_row([
            ("MSE", f"{fit['mse']:.5f}", "plain squared error", "accent"),
            ("RMSE", money(fit["rmse"], 3), "price units", ""),
            ("Mean |IV error|", pct(fit["mean_abs_iv_err"], 2), "market vs model", ""),
            ("Feller 2κθ−σ²", f"{fit['feller']:+.4f}", "≥ 0 required", "warn" if fit["feller"] < 0 else "ok"),
        ]),
        unsafe_allow_html=True,
    )
    st.dataframe(pd.DataFrame([fit["params"]]).round(5), hide_index=True, width="stretch")
    if fit["at_bounds"]:
        st.markdown(callout(f"On an optimiser bound: <b>{', '.join(fit['at_bounds'])}</b> — weakly identified. "
                            "Judge the fit by prices, not by an individual parameter.", "warn"),
                    unsafe_allow_html=True)


d15, d60 = R_["data"]["15"], R_["data"]["60"]
S1a, S1b, S1c, S2a, S2b, S2c, S3a, S3b = (R_[k] for k in ("step1a", "step1b", "step1c", "step2a", "step2b",
                                                           "step2c", "step3a", "step3b"))

tabs = st.tabs(["0 · Data check", "1a · Heston–Lewis", "1b · Heston–Carr-Madan", "1c · Asian call",
                "2a · Bates–Lewis", "2b · Bates–Carr-Madan", "2c · 70-day put", "3a · CIR", "3b · Euribor simulation"])

# ---------------------------------------------------------------- data check
with tabs[0]:
    st.markdown("### Are the supplied quotes internally consistent?")
    st.markdown("Put–call parity requires C − P = S·e^(−qT) − K·e^(−rT) at every common strike. It is the "
                "cheapest arbitrage test available on a quote sheet and it needs no model.")
    for lab, dd in (("15 days", d15), ("60 days", d60)):
        st.markdown(f"**{lab}** — largest violation {money(dd['max_violation'], 2)} · irreducible MSE floor "
                    f"**{dd['floor_mse']:.3f}**")
        st.dataframe(pd.DataFrame(dd["table"]).round(3), hide_index=True, width="stretch")
    st.markdown(
        callout("The sheet is <b>not</b> arbitrage-free: calls and puts disagree by up to ≈$2 at 15 days and ≈$3 at "
                "60 days, and the 60-day calls are not even monotone in strike. Any arbitrage-free model therefore "
                "carries an unavoidable error floor. Every fit below is compared with that floor, not with zero.",
                "warn", "Finding"),
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------- 1a
with tabs[1]:
    st.markdown("### Q1a — Heston (1993) calibrated with Lewis (2001), 15-day options, plain MSE")
    params_table(S1a)
    fit_figs(S1a, "Heston / Lewis, 15d")
    st.markdown("#### Robustness across optimiser seeds")
    st.markdown("Same MSE floor, materially different parameters, essentially the same traded price — the "
                "signature of weak identification.")
    rob = R_["step1_robustness"]
    st.dataframe(pd.DataFrame([{"seed": r["seed"], **{k: round(v, 4) for k, v in r["params"].items()},
                                "MSE": round(r["mse"], 5), "Asian 20d ($)": round(r["asian"], 3)} for r in rob]),
                 hide_index=True, width="stretch")
    pf = R_["step1a_feller"]
    st.markdown(
        f"**Interpretation.** RMSE {money(S1a['rmse'], 3)} against a parity floor of {money(np.sqrt(d15['floor_mse']), 3)}: "
        f"roughly {d15['floor_mse'] / S1a['mse']:.0%} of the squared error is the data, not the model. κ and θ are barely "
        f"identified at a 15-day horizon — a Feller-penalised fit reaches MSE {pf['mse']:.4f} with κ = {pf['params']['kappa']:.2f} "
        f"and θ = {pf['params']['theta']:.3f}. What the quotes *do* pin down is v₀, σ and ρ ≈ −1, i.e. the level, the "
        f"curvature and the strong downside skew.\n\n"
        f"**Procedure.** All ten 15-day quotes (five calls, five puts priced by parity), objective = plain MSE, global "
        f"differential evolution followed by L-BFGS-B polish, r = 1.5 %, T = 15/250, {S1a['n_eval']:,} model evaluations."
    )

# ---------------------------------------------------------------- 1b
with tabs[2]:
    st.markdown("### Q1b — Heston (1993) with the Carr–Madan (1999) transform, 15-day options")
    params_table(S1b)
    fit_figs(S1b, "Heston / Carr-Madan, 15d")
    st.dataframe(pd.DataFrame({"Lewis": list(S1a["params"].values()) + [S1a["mse"]],
                               "Carr–Madan": list(S1b["params"].values()) + [S1b["mse"]]},
                              index=list(S1a["params"]) + ["MSE"]).round(5), width="stretch")
    st.markdown(
        f"**Why the answers agree.** At identical parameters the two transforms differ by at most "
        f"{money(S1b['engine_gap_at_lewis_params'], 5)} — they are two numerical routes to the *same* price function, so "
        f"the fits coincide (MSE {S1a['mse']:.5f} vs {S1b['mse']:.5f}). Parameter vectors can still differ because the "
        f"objective is almost flat in κ and θ; the well-identified parameters (v₀, σ, ρ) agree to several digits."
    )

# ---------------------------------------------------------------- 1c
with tabs[3]:
    st.markdown("### Q1c — Asian call, at the money, 20 days, Monte Carlo, S₀ in the average, 4 % fee")
    qv = S1c["qe"]
    st.markdown(
        kpi_row([
            ("Fair price", money(qv["price"], 4), f"95% CI {delta_span(*qv['ci'], 3)}", "accent"),
            ("Fee (4 %)", money(qv["fee"], 4), "dealer margin", ""),
            ("Client pays", money(qv["client"], 4), "fair + fee", "info"),
            ("vs vanilla", f"{1 - qv['price'] / S1c['vanilla_lewis']:.0%}", "cheaper than ATM vanilla", ""),
        ]),
        unsafe_allow_html=True,
    )
    rows = [("QE — parameters of Q1a (headline)", S1c["qe"]), ("Euler full truncation, same parameters", S1c["euler"]),
            ("QE — Carr–Madan parameters", S1c["qe_cm_params"]),
            ("QE — Feller-penalised parameters", S1c["qe_feller_params"]),
            ("QE — S₀ wrongly excluded from the average", S1c["qe_excl_s0"])]
    st.dataframe(pd.DataFrame([{"Variant": n, "Fair price": round(v["price"], 4),
                                "Std. error": round(v["se"], 4), "Client price (+4 %)": round(v["client"], 4)}
                               for n, v in rows]), hide_index=True, width="stretch")
    ec = S1c["european_check"]
    st.markdown(
        callout(f"Validation: the same Monte Carlo prices a European call at {money(ec['mc'], 4)} against the closed-form "
                f"{money(ec['fourier'], 4)} (z = {ec['z']:+.2f}). Scheme and martingale corrections are therefore consistent.",
                "ok", "Engine check"),
        unsafe_allow_html=True,
    )
    cv = np.array(S1c["convergence"])
    h = S1c["payoff_hist"]
    e = np.array(h["edges"])
    c = st.columns(2, gap="medium")
    with c[0]:
        f = go.Figure(go.Scatter(x=cv[:, 0], y=cv[:, 1], error_y=dict(array=1.96 * cv[:, 2]), mode="markers+lines",
                                 line=dict(color=ACCENT)))
        f.update_layout(title="Monte Carlo convergence (95 % interval)", xaxis_title="Paths", yaxis_title="Price ($)",
                        xaxis_type="log", height=340)
        chart(f)
    with c[1]:
        f = go.Figure(go.Bar(x=(e[:-1] + e[1:]) / 2, y=h["counts"], marker_color=ACCENT))
        f.update_layout(title=f"Discounted payoff distribution ({h['prob_zero']:.0%} pay zero)",
                        xaxis_title="Payoff ($)", yaxis_title="Paths", height=340)
        chart(f)
    st.markdown(
        f"**Plain language.** We first found the assumptions about SM's price and its day-to-day swings that reproduce "
        f"the market's own two-week options. We then simulated {M['n_mc']:,} possible daily price paths for the next 20 "
        f"trading days, computed for each the average price over the period (including today's price) and the payout if "
        f"that average finishes above today's price. Averaging the payouts and discounting at 1.5 % gives the fair value "
        f"of **{money(qv['price'], 2)}**; with the 4 % fee the client pays **{money(qv['client'], 2)}**. Because the payoff "
        f"depends on an average rather than a single date, the option costs less than an ordinary call — and pays less in "
        f"a sharp rally. The result is accurate to a few cents, which is what the confidence interval measures."
    )

# ---------------------------------------------------------------- 2a
with tabs[4]:
    st.markdown("### Q2a — Bates (1996) with jumps, Lewis pricing, 60-day options")
    params_table(S2a)
    fit_figs(S2a, "Bates / Lewis, 60d")
    H = R_["heston60"]
    st.markdown(
        f"**Interpretation.** Bates reaches RMSE {money(S2a['rmse'], 3)} against Heston's {money(H['rmse'], 3)} on the "
        f"same quotes, with a parity floor of {money(np.sqrt(d60['floor_mse']), 3)}. Adding jumps improves the squared "
        f"error by only {1 - S2a['mse'] / H['mse']:.1%}, because {d60['floor_mse'] / S2a['mse']:.0%} of the error is the "
        f"inconsistency in the sheet rather than a missing feature. ρ = {S2a['params']['rho']:+.2f} is atypical for an "
        f"equity and reflects parity violations that grow with strike, not a leverage effect. Eight parameters on ten "
        f"noisy quotes means the jump block should never be read structurally."
    )

# ---------------------------------------------------------------- 2b
with tabs[5]:
    st.markdown("### Q2b — Bates (1996) with the Carr–Madan (1999) transform, 60-day options")
    params_table(S2b)
    fit_figs(S2b, "Bates / Carr-Madan, 60d")
    st.dataframe(pd.DataFrame({"Lewis": list(S2a["params"].values()) + [S2a["mse"]],
                               "Carr–Madan": list(S2b["params"].values()) + [S2b["mse"]]},
                              index=list(S2a["params"]) + ["MSE"]).round(5), width="stretch")
    st.markdown(
        f"At identical parameters the two transforms differ by {money(S2b['engine_gap_at_lewis_params'], 5)}; equal MSE "
        "therefore means equal price functions. Differences in the parameter vector are again loose identification, "
        "so the comparison of interest is on prices."
    )

# ---------------------------------------------------------------- 2c
with tabs[6]:
    st.markdown("### Q2c — European put, 70 days, strike at 95 % of spot")
    mdl = S2c["models"]
    hd = mdl[S2c["headline"]]["mc"]
    st.markdown(
        kpi_row([
            ("Strike", money(S2c["K"], 2), "95 % of spot", ""),
            ("Fair premium", money(hd["price"], 3), f"95% CI {delta_span(*hd['ci'], 3)}", "accent"),
            ("Fee (4 %)", money(hd["fee"], 3), "dealer margin", ""),
            ("Client pays", money(hd["client"], 3), "premium + fee", "info"),
            ("Break-even at expiry", money(S2c["breakeven"], 2), "spot at expiry", ""),
        ]),
        unsafe_allow_html=True,
    )
    names = {"bates_lewis": "Bates, Lewis calibration (headline)", "bates_cm": "Bates, Carr–Madan calibration",
             "bates_feller": "Bates, Feller-penalised", "heston60": "Heston, 60d",
             "heston60_feller": "Heston, 60d Feller-penalised", "heston60_put_quotes_only": "Heston, 60d — puts only",
             "heston60_call_quotes_only": "Heston, 60d — calls only", "heston15_not_appropriate": "Heston, 15d (wrong tenor)"}
    st.dataframe(pd.DataFrame([{"Model / calibration": names[k], "MC price": round(v["mc"]["price"], 4),
                                "Std. error": round(v["mc"]["se"], 4), "Fourier": round(v["fourier"], 4),
                                "z (MC vs Fourier)": round(v["z"], 1), "Client": round(v["mc"]["client"], 3)}
                               for k, v in mdl.items()]), hide_index=True, width="stretch")
    core = [mdl[k]["mc"]["price"] for k in ("bates_lewis", "bates_cm", "bates_feller", "heston60", "heston60_feller")]
    h = S2c["payoff_hist"]
    e = np.array(h["edges"])
    f = go.Figure(go.Bar(x=(e[:-1] + e[1:]) / 2, y=h["counts"], marker_color="#F87171"))
    f.update_layout(title=f"Discounted put payoff ({h['prob_zero']:.0%} of paths expire worthless)",
                    xaxis_title="Payoff ($)", yaxis_title="Paths", height=330)
    chart(f)
    st.markdown(
        f"**Model-risk spread.** Across the five 60-day calibrations the put ranges {money(min(core), 2)}–{money(max(core), 2)}, "
        f"a spread of {money(max(core) - min(core), 2)} on a premium near {money(hd['price'], 2)}. The put-only and call-only "
        f"fits show how much of that spread is the call/put inconsistency in the quote sheet. The 15-day parameters are "
        f"deliberately included to show they are the wrong tenor for a 70-day contract.\n\n"
        f"**Plain language.** A put is insurance. You pay a premium now; if SM is below 95 % of today's price on the expiry "
        f"date, you are compensated for the shortfall. We priced it by simulating {M['n_mc']:,} futures that include "
        f"occasional jumps, then averaged the payouts and discounted them. Most futures finish above the protection level "
        f"and pay nothing; a minority pay a great deal. The figure shows exactly that asymmetry."
    )

# ---------------------------------------------------------------- 3a
with tabs[7]:
    st.markdown("### Q3a — CIR (1985) calibrated to the Euribor term structure")
    ts = S3a["term_structure"]
    st.dataframe(pd.DataFrame({"Maturity": ts["labels"], "Euribor, simple (%)": np.array(ts["simple"]) * 100,
                               "Discount factor": ts["discount"],
                               "Zero rate, continuous (%)": np.array(ts["zero"]) * 100}).round(4),
                 hide_index=True, width="stretch")
    st.markdown(
        "Euribor quotes are **simple** money-market rates, so the discount factor is 1/(1+Lτ) and the continuously "
        "compounded zero rate is ln(1+Lτ)/τ. A cubic spline through the five zero rates gives 52 weekly points over "
        "twelve months, to which the CIR zero-yield curve is fitted with r₀ equal to the one-week rate and the Feller "
        "constraint enforced."
    )
    st.markdown(
        kpi_row([
            ("κ", f"{S3a['kappa']:.3f}", "mean-reversion speed", "accent"),
            ("θ", pct(S3a["theta"], 2), "long-run level", ""),
            ("σ", f"{S3a['sigma']:.3f}", "volatility of the rate", ""),
            ("r₀", pct(S3a["r0"], 3), "one-week rate", ""),
            ("RMSE", f"{S3a['rmse_bp']:.1f} bp", "fit to the spline", "info"),
        ]),
        unsafe_allow_html=True,
    )
    tt = np.array(S3a["t"]) * 12
    pr = np.array(S3a["profile"])
    f1 = go.Figure([
        go.Scatter(x=np.array(ts["tau"]) * 12, y=np.array(ts["zero"]) * 100, mode="markers",
                   name="Euribor zero rates", marker=dict(size=10, color="#F87171")),
        go.Scatter(x=tt, y=np.array(S3a["spline"]) * 100, name="Cubic spline", line=dict(dash="dash")),
        go.Scatter(x=tt, y=np.array(S3a["model"]) * 100, name="CIR"),
    ])
    f1.update_layout(title="CIR fit to the curve", xaxis_title="Maturity (months)", yaxis_title="Zero rate (%)", height=330)
    f2 = go.Figure(go.Bar(x=tt, y=(np.array(S3a["spline"]) - np.array(S3a["model"])) * 1e4, marker_color=ACCENT))
    f2.update_layout(title="Residuals (spline − CIR)", xaxis_title="Maturity (months)", yaxis_title="bp", height=330)
    f3 = go.Figure(go.Scatter(x=pr[:, 0], y=pr[:, 3], mode="lines+markers", line=dict(color="#A78BFA")))
    f3.update_layout(title="σ is not identified by the curve", xaxis_title="Fixed σ", yaxis_title="Best RMSE (bp)", height=330)
    c = st.columns(3)
    for col, fig in zip(c, (f1, f2, f3)):
        with col:
            chart(fig)
    no = S3a["near_optimal"]
    st.markdown(
        f"**Interpretation.** κ = {S3a['kappa']:.2f}, θ = {pct(S3a['theta'], 2)}, σ = {S3a['sigma']:.2f}, RMSE "
        f"{S3a['rmse_bp']:.1f} bp. The steepness of the curve identifies κ and θ, but both extrapolate far beyond the "
        f"twelve-month window of the data. σ is essentially unidentifiable: the fit is equally good for σ between "
        f"{S3a['plateau'][0]:.2f} and {S3a['plateau'][1]:.2f}, so we report the midpoint of that plateau and test the "
        f"sensitivity in Step 3b. Alternative conventions bracket the answer: splining simple rates gives "
        f"{S3a['simple_convention']['rmse_bp']:.1f} bp, and letting r₀ float gives {S3a['free_r0']['rmse_bp']:.1f} bp but "
        f"misses the one-week quote."
    )

# ---------------------------------------------------------------- 3b
with tabs[8]:
    st.markdown("### Q3b — 100,000 exact daily paths of the 12-month Euribor over one year")
    cur, E, cf_ = S3b["current"], S3b["expected"], S3b["conf"]
    st.markdown(
        kpi_row([
            ("Expected in 1 year", pct(E, 2), f"{bp(E - cur, 0, True)} vs today", "accent"),
            ("Today", pct(cur, 3), "market 12M", ""),
            ("95 % low", pct(cf_["0.95"][0], 2), "one-year horizon", "info"),
            ("95 % high", pct(cf_["0.95"][1], 2), "one-year horizon", "info"),
            ("P(above today)", pct(S3b["prob_above_current"], 1), "of 100k paths", ""),
        ]),
        unsafe_allow_html=True,
    )
    st.markdown(caption(f"99 % range at one year {pct(cf_['0.99'][0], 2)} – {pct(cf_['0.99'][1], 2)} · "
                        f"90 % range {pct(cf_['0.90'][0], 2)} – {pct(cf_['0.90'][1], 2)}"), unsafe_allow_html=True)
    days = np.array(S3b["days"])
    f = go.Figure()
    samples = np.array(S3b["samples"])
    for j in range(samples.shape[1]):
        f.add_trace(go.Scatter(x=days, y=samples[:, j] * 100, mode="lines", line=dict(width=.5),
                               opacity=.35, showlegend=False, hoverinfo="skip"))
    f.add_trace(go.Scatter(x=days, y=np.array(S3b["hi95"]) * 100, line=dict(color="#8194AC", width=1),
                           name="97.5th pct"))
    f.add_trace(go.Scatter(x=days, y=np.array(S3b["lo95"]) * 100, line=dict(color="#8194AC", width=1),
                           fill="tonexty", fillcolor="rgba(129,148,172,.14)", name="2.5th pct"))
    f.add_trace(go.Scatter(x=days, y=np.array(S3b["mean_path"]) * 100, line=dict(color=ACCENT, width=3), name="Mean"))
    f.update_layout(title="Simulated 12M Euribor paths with the 95 % band", xaxis_title="Trading day",
                    yaxis_title="12-month Euribor (%)", height=400)
    hh = S3b["hist"]
    ee = np.array(hh["edges"])
    g = go.Figure(go.Bar(x=(ee[:-1] + ee[1:]) / 2, y=hh["counts"], marker_color=ACCENT))
    g.update_layout(title="Distribution at the one-year horizon", xaxis_title="12M Euribor in one year (%)",
                    yaxis_title="Paths", height=400)
    for x_ in cf_["0.95"]:
        g.add_vline(x=x_ * 100, line_dash="dot", line_color="#A78BFA")
    g.add_vline(x=E * 100, line_color=ACCENT)
    g.add_vline(x=cur * 100, line_color="#F87171", line_dash="dash")
    c = st.columns(2, gap="medium")
    with c[0]:
        chart(f)
    with c[1]:
        chart(g)
    st.markdown(
        f"**(i) Range.** At 95 % confidence the 12-month Euribor in one year lies between **{pct(cf_['0.95'][0], 2)} and "
        f"{pct(cf_['0.95'][1], 2)}**. Across the whole year the 95 % envelope spans {pct(S3b['envelope']['95'][0], 2)} to "
        f"{pct(S3b['envelope']['95'][1], 2)}; the extreme values over all 100,000 paths are {pct(S3b['min_all'], 2)} and "
        f"{pct(S3b['max_all'], 2)}.\n\n"
        f"**(ii) Expected value.** **{pct(E, 2)}** in one year against {pct(cur, 3)} today ({bp(E - cur, 0, True)}), with "
        f"{pct(S3b['prob_above_current'], 1)} of paths finishing above today's level. This is the steep current curve "
        f"extrapolated by the fitted model: equally good fits of the same curve give {pct(no['ev_min'], 1)} to "
        f"{pct(no['ev_max'], 1)}. It is a risk-neutral scenario, not a forecast."
    )
    sd = pd.DataFrame(S3b["sigma_sensitivity"])
    st.markdown("#### Sensitivity to the unidentified σ")
    st.markdown("The expected value barely moves while the width scales almost linearly with σ — the honest way to "
                "present a parameter the data cannot pin down.")
    st.dataframe(sd.rename(columns={"sigma": "σ", "mean": "Expected", "lo": "2.5 %", "hi": "97.5 %"}).round(4),
                 hide_index=True, width="stretch")
    imp = S3b["impact"]
    di = pd.DataFrame([{"Rate used": k, "r": v["rate"], "Asian call 20d ($)": round(v["asian20"], 4),
                        "Put 70d ($)": round(v["put70"], 4), "1y discount factor": round(v["discount_1y"], 4)}
                       for k, v in imp.items()])
    st.markdown("#### (iii) Effect on the prices")
    st.dataframe(di, hide_index=True, width="stretch")
    dA = imp["Expected 12M in 1y"]["asian20"] - imp["Today 12M Euribor"]["asian20"]
    dP = imp["Expected 12M in 1y"]["put70"] - imp["Today 12M Euribor"]["put70"]
    st.markdown(
        f"Moving from today's 12-month rate to the expected one changes the 20-day Asian call by **{dA:+.4f}** and the "
        f"70-day put by **{dP:+.4f}**; the one-year discount factor falls from "
        f"{imp['Today 12M Euribor']['discount_1y']:.4f} to {imp['Expected 12M in 1y']['discount_1y']:.4f}. Higher rates "
        f"help calls, hurt puts and reduce discount factors — but at these tenors the volatility assumption dominates. "
        f"For one-year funding or fixed-rate commitments the rate effect is material, which is why it is reported."
    )
    export_row(di, "rate_pricing_impact", "s3b_export")

ai_panel("Assignment Tasks", None, [
    "Summarise the key results of Steps 1–3 for my manager",
    "Why do Lewis and Carr–Madan give nearly the same prices?",
    "What are the weaknesses of the Bates fit?",
])
