
## `SECURITY.md` — 29 lines

```markdown
# Security notes

No public web application can honestly be called "hack proof". This app has been hardened against the realistic abuse paths and checked with automated tools.

## Checked
| Check | Result |
|---|---|
| `pip-audit` on runtime dependencies | Pillow (a Streamlit dependency) had known advisories → pinned `pillow>=13.0.0`. Remaining findings were dev/build-only packages (pypdf, soupsieve) |
| `bandit` static scan | no high-risk code patterns (no `eval/exec/pickle/subprocess/shell`); MD5 used only as a cache key, now flagged `usedforsecurity=False` |
| Secrets | none in the code; keys are read from Streamlit secrets/env only; `.gitignore` and `.dockerignore` exclude `secrets.toml` and `.env` |
| HTML injection / XSS | `unsafe_allow_html` is used only for static strings or escaped text (`html.escape`); no visitor input is ever rendered as HTML |
| Third-party requests | Google Fonts import removed (no visitor IP leak to third parties) |

## Hardening added
- **Upload validation**: ≤1 MB, ≤200 rows, required columns, numeric/range checks, type C/P only, ≤12 maturities.
- **Input bounds**: every number input has min/max; Monte-Carlo size capped (paths × steps ≤ 20 M).
- **Abuse limits**: max 2 heavy calculations at once server-wide, 12 per session per minute (prevents CPU/memory exhaustion).
- **AI limits**: ≤1000 characters per prompt, 30 calls per session, 400 per day, 700-token answers; news/market text is treated as untrusted (prompt-injection guard); the model is fixed server-side.
- **No information leaks**: error details hidden from visitors (`showErrorDetails = none`), generic error messages, toolbar in viewer mode.
- **Server config**: XSRF protection and CORS on, static file serving off, non-root Docker user.

## What you still must do
1. Keep `OPENROUTER_API_KEY` / `FRED_API_KEY` only in Streamlit Cloud *Secrets* – never in GitHub. If a key was ever committed or shared, **rotate it**.
2. Set a spending limit on the OpenRouter key.
3. Enable 2-factor authentication on GitHub and Streamlit accounts; keep the repo private if you do not need it public.
4. Re-run `pip-audit -r requirements.txt` and `pytest` before each deployment.
5. If the app must be private, use Streamlit Cloud's viewer access list or `st.login`.

Report a problem: ajeetk095@gmail.com
