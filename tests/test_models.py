import numpy as np
from utils.models import cf_X
from utils.lewis import lewis_call, cm_call
from utils.cir import cir_yield
H=(.04,1.5,.04,.4,-.6); B=H+(.5,-.1,.15)
def test_martingale(): 
    for m,p in (("heston",H),("bates",B)): assert abs(cf_X(-1j,.25,p,m)-1)<1e-9
def test_cm_equals_lewis():
    for m,p in (("heston",H),("bates",B)): assert abs(lewis_call(100,100,.25,.015,0,p,m)[0]-cm_call(100,100,.25,.015,0,p,m)[0])<5e-3
def test_cir_short(): assert abs(cir_yield(.5,.05,.1,.02,1e-6)-.02)<1e-6
