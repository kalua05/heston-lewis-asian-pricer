import os, re, glob, pandas as pd, pytest
from utils.security import validate_upload, mc_paths, clip
ROOT = os.path.join(os.path.dirname(__file__), "..")
def _df(**kw):
    d = dict(zip(["Days to maturity", "Strike", "Price", "Type"], [15, 230, 10.0, "C"])); d.update(kw)
    return pd.DataFrame([d] * 5)
def test_upload_ok(): assert validate_upload(_df())[1] is None
@pytest.mark.parametrize("kw", [dict(Type="X"), dict(Strike=-5), dict(Price=1e9), {"Days to maturity": 9999}, dict(Strike="abc")])
def test_upload_rejects(kw): assert validate_upload(_df(**kw))[1] is not None
def test_upload_missing_cols(): assert validate_upload(pd.DataFrame({"a": [1]}))[1]
def test_upload_too_many_rows(): assert validate_upload(pd.concat([_df()] * 50))[1]
def test_mc_budget(): assert mc_paths(200_000, 750) * 750 <= 20_000_000 and mc_paths(100_000, 20) == 100_000
def test_clip(): assert clip("a\x00b\x07c" + "x" * 5000, 10) == "abc" + "x" * 7
def test_no_dangerous_calls():
    bad = re.compile(r"\b(eval|exec)\(|pickle\.load|os\.system|shell=True|subprocess\.")
    for f in glob.glob(os.path.join(ROOT, "**", "*.py"), recursive=True):
        if "/tests/" in f or "/scripts/" in f or f.endswith("build_notebook.py"): continue
        assert not bad.search(open(f).read()), f
def test_no_secrets_committed():
    pat = re.compile(r"sk-or-[A-Za-z0-9]{10,}|AKIA[0-9A-Z]{16}|api_key\s*=\s*['\"][A-Za-z0-9]{16,}")
    for f in glob.glob(os.path.join(ROOT, "**", "*.*"), recursive=True):
        if f.endswith((".py", ".toml", ".md", ".txt", ".json", ".example", ".html")) and "/dist/" not in f:
            assert not pat.search(open(f, errors="ignore").read()), f
