"""End-to-end GWP1 computation (Steps 1-3).  One deterministic source of truth for the notebook,
the Streamlit app and the PDF report.  Run ``python -m utils.pipeline`` to refresh results/gwp1_results.json."""
import json, time, sys
from datetime import datetime, timezone
import numpy as np

from . import cir
from .asian_mc import simulate
from .calibration import load_data, calibrate, parity_table, NAMES, feller_gap
from .lewis import lewis_call, cm_call, model_price, implied_vol, greeks
from .paths import DATA_FILE, RESULTS_FILE

S0, R, Q, DPY, FEE = 232.90, 0.015, 0.0, 250, 0.04
N_MC = 200_000


def _j(x):
    """Make numpy objects JSON-serialisable."""
    if hasattr(x, "to_dict") and hasattr(x, "columns"):
        return {c: _j(x[c].astype(object).tolist()) for c in x.columns}
    if isinstance(x, dict): return {k: _j(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [_j(v) for v in x]
    if isinstance(x, np.ndarray): return _j(x.tolist())
    if hasattr(x, "tolist") and not isinstance(x, (str, bytes)) and not np.isscalar(x): return _j(x.tolist())   # pandas / Arrow arrays
    if isinstance(x, (np.floating, float)): return None if not np.isfinite(x) else float(x)
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.bool_,)): return bool(x)
    return x


def _fit(df, res, T, model, method):
    K, typ, mk, md = df.Strike.values, df.Type.values, df.Price.values, res["model"]
    miv = [implied_vol(p, S0, k, T, R, Q, t) for p, k, t in zip(mk, K, typ)]
    viv = [implied_vol(p, S0, k, T, R, Q, t) for p, k, t in zip(md, K, typ)]
    out = {n: float(v) for n, v in zip(res["names"], res["params"])}
    return dict(params=out, mse=res["mse"], rmse=res["rmse"], mae=res["mae"], feller=res["feller"], at_bounds=res["at_bounds"],
                strike=K, type=typ, market=mk, model_price=md, resid=res["residuals"], mkt_iv=miv, mod_iv=viv,
                mean_abs_iv_err=float(np.nanmean(np.abs(np.array(miv) - np.array(viv)))), method=method, model_name=model,
                feller_mode=res["feller_mode"], seed=res["seed"], n_eval=res["n_eval"], T=T)


def _mc(p, K, T, n, payoff, model, seed=42, scheme="qe", r=R, **kw):
    m, se, ci = simulate(S0, K, T, r, Q, p, n, N_MC, seed, model, payoff, scheme, **kw)
    return dict(price=m, se=se, ci=list(ci), client=m * (1 + FEE), fee=m * FEE)


def parity_floor(df, T):
    """Smallest MSE any arbitrage-free model could reach on these quotes (put-call parity violations are irreducible)."""
    pt = parity_table(df, S0, R, Q, T)
    return dict(table=pt, floor_mse=float((pt.Violation ** 2).sum() / (4 * len(pt))), max_violation=float(pt.Violation.abs().max()))


def run_all(maxiter=200, log=print, quick=False):
    t0 = time.time(); out = dict(meta=dict(spot=S0, r=R, q=Q, days_per_year=DPY, fee=FEE, n_mc=N_MC, generated=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                           maxiter=maxiter))
    D = {d: load_data(DATA_FILE, d) for d in (15, 60, 120)}
    T15, T20, T60, T70 = 15 / DPY, 20 / DPY, 60 / DPY, 70 / DPY
    mi = 40 if quick else maxiter

    # ---- data diagnostics
    out["data"] = {str(d): dict(df=df, **parity_floor(df, d / DPY)) for d, df in D.items()}
    log(f"[{time.time()-t0:5.0f}s] data diagnostics")

    # ---- Step 1a / 1b
    L1 = calibrate(D[15], S0, R, Q, T15, "heston", "lewis", maxiter=mi)
    C1 = calibrate(D[15], S0, R, Q, T15, "heston", "cm", maxiter=mi)
    L1f = calibrate(D[15], S0, R, Q, T15, "heston", "lewis", maxiter=mi, feller="penalty")
    out["step1a"] = _fit(D[15], L1, T15, "heston", "lewis")
    out["step1a_feller"] = _fit(D[15], L1f, T15, "heston", "lewis")
    out["step1b"] = _fit(D[15], C1, T15, "heston", "cm")
    # same parameters through both pricers: the two formulas are the same price function
    p1 = L1["params"]; K15 = D[15].Strike.values.astype(float)
    out["step1b"]["engine_gap_at_lewis_params"] = float(np.max(np.abs(lewis_call(S0, K15, T15, R, Q, p1) - cm_call(S0, K15, T15, R, Q, p1))))
    out["step1b"]["engine_gap_at_cm_params"] = float(np.max(np.abs(lewis_call(S0, K15, T15, R, Q, C1["params"]) - cm_call(S0, K15, T15, R, Q, C1["params"]))))
    log(f"[{time.time()-t0:5.0f}s] 1a/1b done  MSE {L1['mse']:.5f}/{C1['mse']:.5f}")
    seeds = []
    for sd in (1, 2, 3) if not quick else (1,):
        rs = calibrate(D[15], S0, R, Q, T15, "heston", "lewis", seed=sd, maxiter=mi)
        a = simulate(S0, S0, T20, R, Q, rs["params"], 20, 100_000, 42, "heston", "asian_call", "qe")
        seeds.append(dict(seed=sd, params=dict(zip(NAMES["heston"], rs["params"])), mse=rs["mse"], asian=a[0], asian_se=a[1]))
    a0 = simulate(S0, S0, T20, R, Q, p1, 20, 100_000, 42, "heston", "asian_call", "qe")
    seeds.insert(0, dict(seed=0, params=dict(zip(NAMES["heston"], p1)), mse=L1["mse"], asian=a0[0], asian_se=a0[1]))
    out["step1_robustness"] = seeds
    log(f"[{time.time()-t0:5.0f}s] 1 robustness")

    # ---- Step 1c  (Asian ATM, 20 days)
    asian = dict(K=S0, T=T20, n_steps=20, params=dict(zip(NAMES["heston"], p1)))
    asian["qe"] = _mc(p1, S0, T20, 20, "asian_call", "heston")
    asian["euler"] = _mc(p1, S0, T20, 20, "asian_call", "heston", scheme="euler")
    asian["qe_cm_params"] = _mc(C1["params"], S0, T20, 20, "asian_call", "heston")
    asian["qe_feller_params"] = _mc(L1f["params"], S0, T20, 20, "asian_call", "heston")
    asian["qe_excl_s0"] = _mc(p1, S0, T20, 20, "asian_call", "heston", include_s0=False)
    asian["vanilla_lewis"] = float(lewis_call(S0, S0, T20, R, Q, p1)[0])
    ec = _mc(p1, S0, T20, 20, "call", "heston")
    asian["european_check"] = dict(mc=ec["price"], se=ec["se"], fourier=asian["vanilla_lewis"], z=(ec["price"] - asian["vanilla_lewis"]) / ec["se"])
    pay = simulate(S0, S0, T20, R, Q, p1, 20, N_MC, 42, "heston", "asian_call", "qe", return_payoffs=True)[1]
    h, e = np.histogram(pay, bins=60); asian["payoff_hist"] = dict(counts=h, edges=e, prob_zero=float((pay == 0).mean()))
    conv = []
    for n in (5_000, 10_000, 25_000, 50_000, 100_000, 200_000):
        m, se, _ = simulate(S0, S0, T20, R, Q, p1, 20, n, 42, "heston", "asian_call", "qe"); conv.append((n, m, se))
    asian["convergence"] = conv
    out["step1c"] = asian
    log(f"[{time.time()-t0:5.0f}s] 1c Asian {asian['qe']['price']:.4f}")

    # ---- Step 2a / 2b (Bates, 60d) + Heston 60d benchmarks
    B_L = calibrate(D[60], S0, R, Q, T60, "bates", "lewis", maxiter=mi)
    B_C = calibrate(D[60], S0, R, Q, T60, "bates", "cm", maxiter=mi)
    B_Lf = calibrate(D[60], S0, R, Q, T60, "bates", "lewis", maxiter=mi, feller="penalty")
    H_L = calibrate(D[60], S0, R, Q, T60, "heston", "lewis", maxiter=mi)
    H_Lf = calibrate(D[60], S0, R, Q, T60, "heston", "lewis", maxiter=mi, feller="penalty")
    out["step2a"] = _fit(D[60], B_L, T60, "bates", "lewis")
    out["step2a_feller"] = _fit(D[60], B_Lf, T60, "bates", "lewis")
    out["step2b"] = _fit(D[60], B_C, T60, "bates", "cm")
    out["heston60"] = _fit(D[60], H_L, T60, "heston", "lewis")
    out["heston60_feller"] = _fit(D[60], H_Lf, T60, "heston", "lewis")
    K60 = D[60].Strike.values.astype(float); pb = B_L["params"]
    out["step2b"]["engine_gap_at_lewis_params"] = float(np.max(np.abs(lewis_call(S0, K60, T60, R, Q, pb, "bates") - cm_call(S0, K60, T60, R, Q, pb, "bates"))))
    dfp, dfc = D[60][D[60].Type == "P"].reset_index(drop=True), D[60][D[60].Type == "C"].reset_index(drop=True)
    H_P = calibrate(dfp, S0, R, Q, T60, "heston", "lewis", maxiter=mi); H_Cc = calibrate(dfc, S0, R, Q, T60, "heston", "lewis", maxiter=mi)
    log(f"[{time.time()-t0:5.0f}s] Step 2 calibrations done  Bates MSE {B_L['mse']:.4f} Heston {H_L['mse']:.4f}")

    # ---- Step 2c  (put 70d, K = 95% S0)
    Kp = 0.95 * S0
    put = dict(K=Kp, T=T70, n_steps=70)
    sets = {"bates_lewis": ("bates", B_L["params"]), "bates_cm": ("bates", B_C["params"]), "bates_feller": ("bates", B_Lf["params"]),
            "heston60": ("heston", H_L["params"]), "heston60_feller": ("heston", H_Lf["params"]),
            "heston60_put_quotes_only": ("heston", H_P["params"]), "heston60_call_quotes_only": ("heston", H_Cc["params"]),
            "heston15_not_appropriate": ("heston", p1)}
    put["models"] = {}
    for k, (mdl, pp) in sets.items():
        fo = float(model_price(S0, Kp, T70, R, Q, pp, "P", mdl)[0])
        mc = _mc(pp, Kp, T70, 70, "put", mdl)
        put["models"][k] = dict(model=mdl, params=dict(zip(NAMES[mdl], pp)), fourier=fo, mc=mc, z=(mc["price"] - fo) / mc["se"])
    put["headline"] = "bates_lewis"
    pay = simulate(S0, Kp, T70, R, Q, B_L["params"], 70, N_MC, 42, "bates", "put", "qe", return_payoffs=True)[1]
    h, e = np.histogram(pay, bins=60); put["payoff_hist"] = dict(counts=h, edges=e, prob_zero=float((pay == 0).mean()))
    put["breakeven"] = Kp - put["models"]["bates_lewis"]["mc"]["price"]
    out["step2c"] = put
    log(f"[{time.time()-t0:5.0f}s] 2c put {put['models']['bates_lewis']['mc']['price']:.4f}")

    # ---- Step 3a / 3b  (CIR on Euribor)
    ts = cir.term_structure(); cr = cir.calibrate_cir("zero"); crs = cir.calibrate_cir("simple")
    t_, y_ = cir.weekly_curve("zero")
    ident = []
    for k in np.linspace(.05, 5, 100):
        for th in np.linspace(.005, .1, 96):
            if cr["sigma"] ** 2 > 2 * k * th: continue
            e_ = np.sqrt(np.mean((y_ - cir.cir_yield(k, th, cr["sigma"], cr["r0"], t_)) ** 2)) * 1e4
            if e_ <= cr["rmse_bp"] + 0.25:
                Er = th + (cr["r0"] - th) * np.exp(-k); g, den, B = cir.cir_zero_params(k, cr["sigma"], 1.0)
                lnA = (2 * k * th / cr["sigma"] ** 2) * np.log(2 * g * np.exp((k + g) / 2) / den)
                ident.append((k, th, e_, float(np.expm1(-lnA + B * Er))))
    ident = np.array(ident)
    sim = cir.simulate_cir_paths(cr["r0"], cr["kappa"], cr["theta"], cr["sigma"], n=100_000)
    Lend = sim["terminal_L12"]; hist, edges = np.histogram(Lend * 100, bins=80)
    ci = {f"{c:.2f}": [float(np.quantile(Lend, (1 - c) / 2)), float(np.quantile(Lend, (1 + c) / 2))] for c in (.90, .95, .99)}
    qi = list(sim["qs"]); lo95, hi95 = sim["quantiles"][:, qi.index(.025)], sim["quantiles"][:, qi.index(.975)]
    lo99, hi99 = sim["quantiles"][:, qi.index(.005)], sim["quantiles"][:, qi.index(.995)]
    sig_sens = []
    for s_ in (.02, .05, .10, .20, .30):
        sm = cir.simulate_cir_paths(cr["r0"], cr["kappa"], cr["theta"], s_, n=20_000, n_sample=1); Lt = sm["terminal_L12"]
        sig_sens.append(dict(sigma=s_, mean=float(Lt.mean()), lo=float(np.quantile(Lt, .025)), hi=float(np.quantile(Lt, .975))))
    # free-r0 sensitivity
    from scipy.optimize import minimize as _min
    rm = lambda z: np.sqrt(np.mean((y_ - cir.cir_yield(z[0], z[1], z[2], z[3], t_)) ** 2)) * 1e4
    fr = min((_min(lambda z: rm(z) + 1e3 * max(0, z[2] ** 2 - 2 * z[0] * z[1]), x0, bounds=[(1e-3, 5), (1e-3, .1), (1e-3, 1), (1e-4, .03)], method="L-BFGS-B")
              for x0 in ([.8, .06, .17, .006], [2, .04, .3, .005], [.3, .1, .1, .007], [1.5, .05, .2, .004])), key=lambda o: o.fun)
    Er = fr.x[1] + (fr.x[3] - fr.x[1]) * np.exp(-fr.x[0]); g, den, B = cir.cir_zero_params(fr.x[0], fr.x[2], 1.0)
    lnA = (2 * fr.x[0] * fr.x[1] / fr.x[2] ** 2) * np.log(2 * g * np.exp((fr.x[0] + g) / 2) / den)
    cur = float(cir.QUOTES[-1]); Eend = float(Lend.mean())
    out["step3a"] = dict(term_structure=ts, kappa=cr["kappa"], theta=cr["theta"], sigma=cr["sigma"], r0=cr["r0"], rmse_bp=cr["rmse_bp"], feller=cr["feller"],
                         t=cr["t"], spline=cr["market"], model=cr["model"], profile=cr["profile"], plateau=cr["plateau"],
                         simple_convention=dict(kappa=crs["kappa"], theta=crs["theta"], sigma=crs["sigma"], rmse_bp=crs["rmse_bp"]),
                         free_r0=dict(kappa=fr.x[0], theta=fr.x[1], sigma=fr.x[2], r0=fr.x[3], rmse_bp=float(rm(fr.x)), expected_12m_1y=float(np.expm1(-lnA + B * Er))),
                         near_optimal=dict(n=len(ident), ev_min=float(ident[:, 3].min()), ev_max=float(ident[:, 3].max()),
                                           kappa_min=float(ident[:, 0].min()), kappa_max=float(ident[:, 0].max()), theta_min=float(ident[:, 1].min()), theta_max=float(ident[:, 1].max())),
                         model_12m_today=float(sim["mean"][0]), market_12m_today=cur)
    out["step3b"] = dict(n_paths=100_000, n_steps=250, current=cur, expected=Eend, expected_sd=float(Lend.std()), analytic_mean_short_rate=sim["analytic_mean_r"], sim_mean_short_rate=float(sim["terminal_r"].mean()),
                         conf=ci, min_all=float(sim["path_min"].min()), max_all=float(sim["path_max"].max()),
                         envelope={"95": [float(lo95.min()), float(hi95.max())], "99": [float(lo99.min()), float(hi99.max())]},
                         pathwise=dict(min_median=float(np.median(sim["path_min"])), max_median=float(np.median(sim["path_max"])), min_p5=float(np.quantile(sim["path_min"], .05)),
                                       max_p95=float(np.quantile(sim["path_max"], .95))),
                         prob_above_current=float((Lend > cur).mean()), days=sim["days"], mean_path=sim["mean"], lo95=lo95, hi95=hi95, lo99=lo99, hi99=hi99, median=sim["quantiles"][:, qi.index(.5)],
                         samples=sim["samples"], hist=dict(counts=hist, edges=edges), sigma_sensitivity=sig_sens)
    log(f"[{time.time()-t0:5.0f}s] Step 3 done  E[L12(1y)] {Eend:.4%}")

    # ---- Step 3b (iii): pricing impact of the expected 12M rate
    rates = {"Brief constant (1.50%)": R, "Today 12M Euribor": cur, "Expected 12M in 1y": Eend,
             "95% low (1y)": ci["0.95"][0], "95% high (1y)": ci["0.95"][1]}
    imp = {}
    for nm, rr in rates.items():
        a = simulate(S0, S0, T20, rr, Q, p1, 20, 100_000, 7, "heston", "asian_call", "qe")[0]
        pt = simulate(S0, Kp, T70, rr, Q, B_L["params"], 70, 100_000, 7, "bates", "put", "qe")[0]
        imp[nm] = dict(rate=rr, asian20=a, put70=pt, vanilla_call20=float(lewis_call(S0, S0, T20, rr, Q, p1)[0]),
                       put70_fourier=float(model_price(S0, Kp, T70, rr, Q, B_L["params"], "P", "bates")[0]), discount_1y=float(1 / (1 + rr)))
    out["step3b"]["impact"] = imp
    out["meta"]["elapsed_s"] = time.time() - t0
    log(f"[{time.time()-t0:5.0f}s] pipeline complete")
    return _j(out)


def save(res, path=RESULTS_FILE):
    path.parent.mkdir(parents=True, exist_ok=True)
    def default(o):
        if hasattr(o, "to_dict"): return o.to_dict(orient="list")
        raise TypeError(type(o))
    path.write_text(json.dumps(res, default=default))
    return path


def load(path=RESULTS_FILE):
    return json.loads(path.read_text()) if path.exists() else None


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    res = run_all(quick=quick)
    json.dumps(res, default=lambda o: o.to_dict(orient="list"))   # fail early, before anything is lost
    print("saved", save(res, RESULTS_FILE.with_name("gwp1_results_quick.json") if quick else RESULTS_FILE))
