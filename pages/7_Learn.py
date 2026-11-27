import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import *
from utils.theme import badge, callout, kpi_row, page_header

setup("Learn the Model", "🎓")

st.markdown(
    page_header(
        "Learn the model",
        "Five short lessons that take a reader from stochastic volatility to a tradable price, plus the "
        "questions examiners and clients actually ask.",
        kicker="Reference",
        meta=[badge("5 lessons", "info"), badge("No maths beyond calculus", "neutral")],
    ),
    unsafe_allow_html=True,
)

lessons = st.tabs(["1 · Stochastic volatility", "2 · Why Fourier", "3 · Calibration", "4 · Asian options", "5 · FAQ"])

with lessons[0]:
    st.markdown(
        "Black–Scholes assumes volatility is a constant. Markets disagree: implied volatility varies with strike "
        "(the **skew**) and with maturity (the **term structure**). Heston (1993) lets variance itself be random:\n\n"
    )
    st.latex(r"dS_t = r S_t\,dt + \sqrt{v_t}\,S_t\,dW^S_t")
    st.latex(r"dv_t = \kappa(\theta - v_t)\,dt + \sigma\sqrt{v_t}\,dW^v_t, \qquad d\langle W^S, W^v\rangle = \rho\,dt")
    st.markdown(
        "- **v₀** sets the level of volatility today, hence the overall price level.\n"
        "- **κ** is how fast variance is pulled back to **θ**, its long-run level.\n"
        "- **σ** is volatility *of* volatility: it controls how curved the smile is.\n"
        "- **ρ** links price and variance shocks. Negative ρ means volatility rises when prices fall — exactly the "
        "equity skew.\n\n"
        "The **Feller condition** 2κθ ≥ σ² keeps variance strictly positive. When it fails, variance can touch zero and "
        "the discretisation scheme starts to matter — which is why the app simulates with Andersen's QE scheme by default."
    )

with lessons[1]:
    st.markdown(
        "The Heston transition density has no closed form, so pricing by integrating it directly would be slow and "
        "noisy. But its **characteristic function** is closed form:\n\n"
    )
    st.latex(r"\phi(u) = \mathbb{E}\left[e^{iuX_T}\right], \qquad X_T = \ln(S_T/F_T)")
    st.markdown(
        "Lewis (2001) turns the option price into a single integral against that transform (with ν = ½):"
    )
    st.latex(r"C = S e^{-qT} - \frac{\sqrt{SK}\,e^{-(r+q)T/2}}{\pi}\int_0^\infty "
             r"\frac{\operatorname{Re}\left[e^{iuk}\phi(u-\tfrac{i}{2})\right]}{u^2+\tfrac14}\,du, "
             r"\qquad k = \ln(S/K) + (r-q)T")
    st.markdown(
        "Carr–Madan (1999) damps the payoff with e^(−αk) and integrates along a shifted line instead. Both are exact; "
        "they differ only in how the integrand decays, which is why the app shows them agreeing to a fraction of a cent.\n\n"
        "The integral is evaluated with composite **Gauss–Legendre** quadrature: 16-point panels of width 5 out to "
        "U_max = 400. That is roughly three times faster than a dense trapezoid grid at the same accuracy, which is what "
        "makes a calibration inside a web request feasible."
    )

with lessons[2]:
    st.markdown(
        "Calibration is a least-squares problem with no useful derivative information:\n\n"
        "1. Load the quotes for one maturity (puts become model puts by put–call parity).\n"
        "2. Price them all with the Fourier engine for a candidate parameter vector.\n"
        "3. Minimise the **plain mean squared price error**.\n"
        "4. Global search with differential evolution, then a bounded L-BFGS-B polish.\n"
        "5. Sanity-check: Feller margin, parameters sitting on bounds, residual pattern, implied-vol fit.\n\n"
        "Two results from this project are worth remembering. First, the objective is extremely flat in κ and θ at a "
        "fifteen-day horizon — many parameter pairs fit equally well, and a Feller penalty moves the parameters "
        "completely while changing the MSE by a tenth of a percent. Second, when the quote sheet violates put–call "
        "parity, **part of the error is not the model's fault**: that is the irreducible MSE floor shown on every fit."
    )

with lessons[3]:
    st.markdown(
        "An Asian option pays on the **average** price over a monitoring period:\n\n"
    )
    st.latex(r"\text{Payoff} = \max\left(\frac{1}{n+1}\sum_{i=0}^{n} S_{t_i} - K,\; 0\right)")
    st.markdown(
        "Note the sum starts at i = 0: **today's spot is the first fixing**, so n steps give n + 1 points. Getting that "
        "wrong is a classic error and changes the price by several cents — the app prices both variants so the size of "
        "the mistake is visible.\n\n"
        "Averaging reduces the variance of the payoff, so an Asian call is always cheaper than the vanilla with the same "
        "strike. It also caps the upside: exactly what a corporate hedger wants, and exactly what an option buyer may "
        "not want.\n\n"
        "Monte Carlo specifics: Andersen's **quadratic-exponential** scheme for the variance, with the martingale "
        "correction applied to the log-price step so that E[S_T] equals the forward. Antithetic variates halve the "
        "variance, and the reported standard error uses the pair averages."
    )

with lessons[4]:
    st.markdown(
        "**Why not match the smile at 15 days?** One-factor Heston is too smooth for very short expiries; the data "
        "want a jump component or a much richer volatility process. That is the motivation for Bates.\n\n"
        "**Why QE rather than Euler?** With a short-dated, high vol-of-vol calibration the Feller condition can fail. "
        "Full-truncation Euler then biases the variance and the price; QE keeps the transition distribution correct.\n\n"
        "**Why is ρ sometimes positive in the fits?** Because the quotes themselves are inconsistent. A positive ρ "
        "would be economically odd for an equity, and it appears here as the optimiser compensating for parity "
        "violations that grow with strike.\n\n"
        "**Why report prices instead of parameters?** Because the parameters are weakly identified while the prices are "
        "stable. A model that reproduces the market is useful even when several parameter vectors do the job.\n\n"
        "**What would you do with more data?** Add maturities between 15 and 60 days so κ and θ are identified by the "
        "term structure rather than by a single slice, and calibrate only to out-of-the-money quotes where liquidity "
        "is genuine."
    )

ai_panel("Learn", None, ["Explain the Heston model to a 15-year-old", "Why does S₀ belong in the Asian average?",
                         "What does the Feller condition mean?"])
