# User guide

A task-oriented walkthrough of the SM Energy Pricer. Every section answers one question a reader actually asks:
*where do I click, what does the number mean, and what should I not conclude from it?*

---

## 1. Before you start

| Requirement | Detail |
|---|---|
| Python | 3.11 or newer (`python3 --version`) |
| Disk | ≈200 MB with the virtual environment |
| Browser | Any current Chrome, Firefox, Safari or Edge |
| API keys | **Optional.** Only the AI assistant and the FRED rate feed use them |

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
