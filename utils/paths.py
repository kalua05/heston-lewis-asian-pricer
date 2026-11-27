"""Project paths that do not depend on the current working directory.

``DATA_FILE`` accepts either the Excel workbook shipped with the project or a
plain CSV with the same columns, so the app runs without Excel installed.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
_XLSX = DATA_DIR / "option_data.xlsx"
_CSV = DATA_DIR / "option_data.csv"
DATA_FILE = _XLSX if _XLSX.exists() else _CSV
RESULTS_FILE = ROOT / "results" / "gwp1_results.json"
REPORT_DIR = ROOT / "reports"
NOTEBOOK_DIR = ROOT / "notebooks"
DOC_DIR = ROOT / "documentation"
