# Deployment

The app needs no secrets to show the assignment results (pre-computed in `results/gwp1_results.json`; if that file is missing it recomputes a quick version on first load). Python 3.11+.

**Streamlit Community Cloud (simplest, free):** push this folder to a GitHub repository → share.streamlit.io → *New app* → repository, branch `main`, main file `app.py` → *Advanced settings* → Python 3.11. Optional secrets: `OPENROUTER_API_KEY`, `FRED_API_KEY`. Do not commit secrets.

**Docker (any host):**
```bash
docker build -t gwp1-app .
docker run -p 8501:8501 gwp1-app            # add --env-file .env for optional API keys
# health check: curl http://localhost:8501/_stcore/health  -> ok
