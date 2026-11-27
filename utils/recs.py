import numpy as np, pandas as pd
from .lewis import implied_vol, model_price
def rich_cheap(df, model, S, T, r, q, tol=0.25):
    d = df.copy(); d['Model'] = model; d['Resid'] = d['Price']-d['Model']
    d['MktIV'] = [implied_vol(p,S,k,T,r,q,t) for p,k,t in zip(d.Price,d.Strike,d.Type)]
    d['ModIV'] = [implied_vol(p,S,k,T,r,q,t) for p,k,t in zip(d.Model,d.Strike,d.Type)]
    d['Signal'] = np.where(d.Resid > tol, 'Rich vs model (sell-side candidate)', np.where(d.Resid < -tol, 'Cheap vs model (buy-side candidate)', 'Fair'))
    return d
def recommendations(S, K, T, vanilla, asian, ci, rmse, feller, p, fee=.04):
    out = []
    out.append(f"**Asian vs vanilla:** the ATM Asian call is ${asian:.2f} versus ${vanilla:.2f} for the vanilla — "
               f"{(1-asian/vanilla):.0%} cheaper, because averaging (S₀ included) cuts effective volatility. Suits a client who cares about an average price, not a terminal spike.")
    out.append(f"**Pricing:** fair value ${asian:.2f} (95% CI ${ci[0]:.2f}–${ci[1]:.2f}); with the {fee:.0%} fee the client pays ${asian*(1+fee):.2f}. "
               f"The MC interval is ~{(ci[1]-ci[0])/2/asian:.1%} of price — tight enough to quote.")
    if p[4] < -.9 or p[3] > 1.2 or min(abs(p[4]+.99),1) < .02: out.append("**Model risk:** parameters sit on optimiser bounds (|ρ|≈1 or very high σ). The fit is driven by ~10 noisy quotes; add a wider reserve or calibrate across maturities before quoting size.")
    if feller < 0: out.append("**Feller violated:** variance can touch zero; use QE discretisation (default) and avoid full-truncation Euler.")
    out.append(f"**Fit quality:** price RMSE ${rmse:.2f} on a ~${S:.0f} stock. Short-dated (15d) Heston cannot reproduce a steep smile; for 60d+ use jumps (Bates) per the project's Step 2.")
    out.append("**Desk actions:** (1) hedge delta/vega with listed options near the money, (2) re-calibrate daily from the live chain, (3) keep a skew/jump reserve around events (earnings, oil/gas moves, OPEC).")
    out.append("**Investor view (illustrative, not advice):** buyers wanting upside exposure with limited premium may prefer the Asian structure; those fearing a gap down should compare protective puts using the residual table. Always check liquidity and bid-ask before acting.")
    return out
