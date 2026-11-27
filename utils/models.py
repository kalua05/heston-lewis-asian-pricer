import numpy as np
from .heston import heston_cf
def cf_X(z, T, p, model="heston"):
    """E[exp(i z X_T)], X_T=ln(S_T/F_T), martingale-normalised (phi(-i)=1). Heston p=5 params; Bates p=8."""
    h = heston_cf(z, T, *p[:5])
    if model == "heston": return h
    lam, mu, dl = p[5:8]; kb = np.exp(mu+.5*dl**2)-1
    return h*np.exp(lam*T*(np.exp(1j*z*mu-.5*z**2*dl**2)-1) - 1j*z*lam*kb*T)
