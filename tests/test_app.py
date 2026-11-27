from streamlit.testing.v1 import AppTest
import pytest, os, glob
ROOT = os.path.join(os.path.dirname(__file__), "..")
FILES = ["app.py"] + sorted(os.path.relpath(f, ROOT) for f in glob.glob(os.path.join(ROOT, "pages", "*.py")))
@pytest.mark.parametrize("f", FILES)
def test_pages(f):
    at = AppTest.from_file(os.path.join(ROOT, f), default_timeout=240).run()
    assert not at.exception, at.exception
