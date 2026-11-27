from utils.lewis import lewis_call, bs
from utils.asian_mc import asian_call_mc
def test_lewis_matches_bs_when_volvol_tiny():
    p=(.04,1.,.04,1e-2,0.)
    assert abs(lewis_call(100,100,.5,.02,0,p)[0]-bs(100,100,.5,.02,0,.2,'C'))<5e-3
def test_asian_below_european():
    p=(.04,1.,.04,.3,-.7); a,se,_=asian_call_mc(100,100,.25,.02,0,p,60,40000)
    assert 0<a<lewis_call(100,100,.25,.02,0,p)[0]
