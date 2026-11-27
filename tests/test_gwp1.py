"""Regression tests for the corrected GWP1 code (fast: no long optimisations)."""
import numpy as np, pytest
from scipy.integrate import quad
from utils.models import cf_X
from utils.lewis import lewis_call, cm_call, model_price
from utils.asian_mc import simulate
from utils import cir
from utils.calibration import load_data, parity_table, calibrate, feller_gap
from utils.paths import DATA_FILE

S, r, q = 232.9, .015, 0.
H = (.085, 3.7, .25, 1.35, -.99)
B = (.04, .8, .5, .9, .96, .44, .26, .002)


def exact_lewis(K, T, p, model):
    k = np.log(S / K) + (r - q) * T
    f = lambda u: (np.exp(1j * u * k) * cf_X(u - .5j, T, p, model)).real / (u * u + .25)
    return S - np.sqrt(S * K) * np.exp(-(r + q) * T / 2) / np.pi * quad(f, 0, np.inf, limit=4000, epsabs=1e-12, epsrel=1e-12)[0]


@pytest.mark.parametrize("p,model", [(H, "heston"), (B, "bates")])
@pytest.mark.parametrize("days", [5, 20, 60, 70])
def test_fourier_pricers_match_exact_integration(p, model, days):
    T = days / 250
    for K in (200., 221.3, 232.9, 255.):
        ex = exact_lewis(K, T, p, model)
        assert abs(lewis_call(S, K, T, r, q, p, model)[0] - ex) < 5e-3
        assert abs(cm_call(S, K, T, r, q, p, model)[0] - ex) < 1.5e-2


def test_put_call_parity_in_model_price():
    K = np.array([220., 240.]); c = model_price(S, K, .1, r, q, H, np.array(["C", "C"])); p = model_price(S, K, .1, r, q, H, np.array(["P", "P"]))
    assert np.allclose(c - p, S - K * np.exp(-r * .1))


@pytest.mark.parametrize("p,model", [(H, "heston"), (B, "bates")])
def test_qe_mc_matches_fourier_european_prices(p, model):
    T = 70 / 250
    for kind, typ, K in (("put", "P", .95 * S), ("call", "C", S)):
        fo = float(model_price(S, K, T, r, q, p, typ, model)[0]); m, se, _ = simulate(S, K, T, r, q, p, 70, 150_000, 3, model, kind)
        assert abs(m - fo) < 4 * se + 0.01


def test_asian_includes_s0_and_is_cheaper_than_vanilla():
    p = (.04, 1.5, .04, .4, -.6); T = 20 / 250
    a = simulate(S, S, T, r, q, p, 20, 60_000, 1, payoff="asian_call")[0]
    wrong = simulate(S, S, T, r, q, p, 20, 60_000, 1, payoff="asian_call", include_s0=False)[0]
    assert 0 < a < float(lewis_call(S, S, T, r, q, p)[0]) and a < wrong      # S0 in the average lowers an ATM call slightly


def test_mc_is_reproducible_and_validates_inputs():
    p = (.04, 1.5, .04, .4, -.6)
    assert simulate(S, S, .08, r, q, p, 20, 4000, 5)[0] == simulate(S, S, .08, r, q, p, 20, 4000, 5)[0]
    with pytest.raises(ValueError): simulate(S, S, .08, r, q, p, 20, 4000, 5, payoff="x")


def test_data_file_and_parity_floor():
    df = load_data(DATA_FILE, 60); assert len(df) == 10
    pt = parity_table(df, S, r, q, 60 / 250); assert pt.Violation.abs().max() > 1       # the quotes are parity-inconsistent


def test_calibration_returns_regular_mse_and_recovers_synthetic_prices():
    import pandas as pd
    T = 30 / 250; K = np.linspace(215, 250, 8); p = (.05, 2.0, .06, .5, -.6)
    df = pd.DataFrame({"Strike": K, "Type": ["C"] * 8, "Price": model_price(S, K, T, r, q, p, np.array(["C"] * 8))})
    res = calibrate(df, S, r, q, T, "heston", maxiter=60, popsize=12)
    assert res["mse"] < 1e-3 and res["objective"] == pytest.approx(res["mse"])


def test_cir_term_structure_and_calibration():
    ts = cir.term_structure(); assert np.all(np.diff(ts["discount"]) < 0) and np.allclose(cir.zero_to_simple(ts["zero"], ts["tau"]), cir.QUOTES)
    c = cir.calibrate_cir(); assert c["rmse_bp"] < 12 and c["feller"] >= -1e-9 and len(c["t"]) == 52


def test_cir_simulation_mean_matches_analytic_and_bands_are_ordered():
    c = cir.calibrate_cir(); s = cir.simulate_cir_paths(c["r0"], c["kappa"], c["theta"], c["sigma"], n=20_000)
    assert abs(s["terminal_r"].mean() - s["analytic_mean_r"]) < 4 * s["terminal_r"].std() / np.sqrt(20_000)
    qs = list(s["qs"]); assert np.all(s["quantiles"][:, qs.index(.975)] >= s["quantiles"][:, qs.index(.025)])
    assert (s["path_min"] <= s["terminal_L12"]).all() and (s["path_max"] >= s["terminal_L12"]).all() and len(s["days"]) == 251


def test_results_serialisation():
    import json
    from utils.pipeline import _j, parity_floor
    json.dumps(_j(dict(x=np.float64(1), a=np.arange(3), p=parity_floor(load_data(DATA_FILE, 15), .06))))
