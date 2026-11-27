"""Build the GWP1 presentation from the pipeline results (no hard-coded numbers)."""
import os, tempfile
from pptx import Presentation
from pptx.util import Pt


def slides(R):
    a, p, c, b = R["step1a"], R["step2c"], R["step3a"], R["step3b"]
    put = p["models"][p["headline"]]["mc"]; s1 = R["step1c"]["qe"]; d15, d60 = R["data"]["15"], R["data"]["60"]
    return [
        ("MScFE 622 GWP1: SM Energy options and Euribor scenarios", "Heston, Bates, Asian call, put and CIR\nCalibration with Lewis (2001) and Carr-Madan (1999)"),
        ("Problem and data", f"Price an Asian call and a put on SM, and scenario-test the 12M Euribor.\nSpot $232.90, r = 1.50%, 250 days/year. Quotes at 15, 60, 120 days; Euribor 1w-12m."),
        ("Data quality", f"Calls and puts violate put-call parity (max gap ${d15['max_violation']:.2f} at 15d, ${d60['max_violation']:.2f} at 60d).\nIrreducible MSE floor: {d15['floor_mse']:.3f} (15d), {d60['floor_mse']:.3f} (60d)."),
        ("Step 1: Heston, 15 days", f"Lewis and Carr-Madan: same fit (MSE {a['mse']:.4f}), same price function.\nParameters kappa/theta weakly identified; v0, sigma, rho well identified."),
        ("Step 1c: Asian call (ATM, 20 days)", f"Fair ${s1['price']:.2f} +/- {s1['se']:.3f}; client pays ${s1['client']:.2f} (4% fee).\nS0 in the average; QE scheme with martingale correction; validated against closed form."),
        ("Step 2: Bates, 60 days", f"Bates MSE {R['step2a']['mse']:.3f} vs Heston {R['heston60']['mse']:.3f}.\nMost residual error is put-call inconsistency, not model misspecification."),
        ("Step 2c: Put, 70 days, 95% moneyness", f"Fair ${put['price']:.2f}; client pays ${put['client']:.2f}.\nBates Monte Carlo with jumps, validated against the Fourier price."),
        ("Step 3a: CIR on Euribor", f"kappa {c['kappa']:.2f}, theta {c['theta']:.2%}, sigma {c['sigma']:.2f}; RMSE {c['rmse_bp']:.1f} bp.\nSigma is not identified by the curve; sensitivity reported."),
        ("Step 3b: 12M Euribor in one year", f"Expected {b['expected']:.2%} vs {b['current']:.3%} today.\n95% range {b['conf']['0.95'][0]:.2%} to {b['conf']['0.95'][1]:.2%} (100,000 daily paths)."),
        ("Limits and next steps", "Fit calls and puts on a parity-consistent data set; add a longer maturity for Bates; calibrate CIR with rate-option data to identify sigma.\nResearch use only; not financial advice."),
    ]


def build(R, path=None):
    path = path or os.path.join(tempfile.gettempdir(), "gwp1_deck.pptx")
    pr = Presentation()
    for i, (t, body) in enumerate(slides(R)):
        s = pr.slides.add_slide(pr.slide_layouts[0 if i == 0 else 1]); s.shapes.title.text = t
        tf = s.placeholders[1].text_frame; tf.text = body
        for para in tf.paragraphs:
            for r in para.runs: r.font.size = Pt(20)
    pr.save(path); return path
