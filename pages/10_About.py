import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import *
from utils.theme import badge, callout, page_header

setup("About & Docs", "ℹ️")

st.markdown(
    page_header(
        "About the project",
        "Who built it, what it is for, how it is deployed and what its limits are — including the security posture "
        "and the honest disclaimer.",
        kicker="Reference",
        meta=[badge("Research use only", "warn"), badge("MIT licensed", "neutral")],
    ),
    unsafe_allow_html=True,
)

tab_about, tab_docs, tab_security, tab_contact, tab_legal = st.tabs(
    ["Author", "Documentation", "Security", "Contact", "Disclaimer"]
)

# ---------------------------------------------------------------- author
with tab_about:
    c1, c2 = st.columns([1, 2.2], gap="medium")
    with c1:
        avatar = ROOT / "assets" / "profile.png"
        if avatar.exists():
            st.image(str(avatar), width=180)
        else:
            st.markdown(
                "<div style='width:180px;height:180px;border-radius:16px;display:grid;place-items:center;"
                "background:var(--surface-2);border:1px solid var(--border);font-size:2.4rem;font-weight:800;"
                "color:var(--accent)'>AK</div>",
                unsafe_allow_html=True,
            )
    with c2:
        st.markdown("### Ajeet Kumar")
        st.markdown(
            "Quantitative finance practitioner based in Bangalore. B.Tech in Information Technology (AKTU), "
            "M.Tech in Computer Science (NSUT, CGPA 7.92) and an M.Sc. in Financial Engineering from WorldQuant "
            "University (88 %). First place at the Algo8 ML Hackathon (IIT Kanpur), felicitated by the President of India."
        )
        st.markdown(
            "**Focus areas.** Stochastic volatility and Fourier pricing, Monte Carlo methods, portfolio optimisation "
            "(MVO, Black–Litterman), machine learning and reinforcement learning applied to markets."
        )
        st.markdown(
            "**How this project was built.** Read Lewis (2001) → understand the quote sheet (and discover it violates "
            "put–call parity) → calibrate Heston and Bates → price the Asian and the put by Monte Carlo → calibrate CIR "
            "to Euribor → rebuild the app, notebook and report from a single results file."
        )
        b = st.columns(3)
        b[0].link_button("LinkedIn", "https://www.linkedin.com/in/ajeek095/", width="stretch")
        b[1].link_button("GitHub", "https://github.com/ajeetk095", width="stretch")
        b[2].link_button("Email", "mailto:ajeetk095@gmail.com", width="stretch")

    st.markdown("## What this project demonstrates")
    st.markdown(
        "- **Theory to code.** A published transform (Lewis 2001) implemented with quadrature fast enough to calibrate "
        "inside a web request, cross-validated against adaptive integration.\n"
        "- **Numerical honesty.** Schemes are compared, not assumed: QE against Euler, Lewis against Carr–Madan, "
        "Monte Carlo against closed form.\n"
        "- **Research judgement.** The weakest part of the data (parity violations, weak identification) is quantified "
        "and reported rather than hidden.\n"
        "- **Engineering.** One results file feeds the app, the notebook, the report and the deck; typed helpers, "
        "bounded inputs, throttling, tests and container deployment."
    )

# ---------------------------------------------------------------- docs
with tab_docs:
    st.markdown("### Bundled documents")
    docs = [("README.md", "Quick start, structure and rebuild commands"),
            ("USER_GUIDE.md", "Task-by-task usage guide with screenshots"),
            ("deployment.md", "Streamlit Cloud, Docker, Render, Hugging Face Spaces"),
            ("documentation/CORRECTIONS.md", "Audit log: what was wrong and how it was verified"),
            ("SECURITY.md", "Threat model, hardening and what the operator must still do"),
            ("CHANGELOG.md", "This refactor, file by file")]
    for file, desc in docs:
        p = ROOT / file
        col = st.columns([2.2, 3, 1])
        col[0].markdown(f"**{file}**")
        col[1].markdown(f"<div class='gsq-cap'>{esc(desc)}</div>", unsafe_allow_html=True)
        if p.exists():
            col[2].download_button("⬇", p.read_bytes(), p.name, key=f"doc_{file.replace('/', '_')}",
                                   width="stretch")
        else:
            col[2].markdown(caption("missing"), unsafe_allow_html=True)

    st.markdown("### Read inline")
    pick = st.selectbox("Document", [f for f, _ in docs if (ROOT / f).exists()], key="doc_pick")
    if pick:
        st.markdown((ROOT / pick).read_text())

# ---------------------------------------------------------------- security
with tab_security:
    sec = ROOT / "SECURITY.md"
    if sec.exists():
        st.markdown(sec.read_text())
    else:
        st.markdown(callout("SECURITY.md not found.", "warn"), unsafe_allow_html=True)

# ---------------------------------------------------------------- contact
with tab_contact:
    st.markdown("### Send a message")
    st.markdown("<div class='gsq-cap'>This form validates your input and opens your own mail client — nothing is "
                "transmitted or stored by the app.</div>", unsafe_allow_html=True)
    n = clip(st.text_input("Name", max_chars=80, key="ct_n"), 80)
    e = clip(st.text_input("Email", max_chars=120, key="ct_e"), 120)
    msg = clip(st.text_area("Message", max_chars=1500, key="ct_m", height=140), 1500)
    if st.button("Validate and open mail client", type="primary"):
        from urllib.parse import quote
        if not n.strip() or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", e) or len(msg.strip()) < 10:
            st.error("Enter a name, a valid email address and a message of at least 10 characters.")
        else:
            st.success("Looks good — the button below opens your mail client with the message pre-filled.")
            st.link_button("Open email",
                           f"mailto:ajeetk095@gmail.com?subject={quote('Heston-Lewis app: ' + n)}"
                           f"&body={quote(msg + chr(10) + chr(10) + e)}")
    c = st.columns(3)
    c[0].link_button("Email", "mailto:ajeetk095@gmail.com", width="stretch")
    c[1].link_button("LinkedIn", "https://www.linkedin.com/in/ajeek095/", width="stretch")
    c[2].link_button("GitHub", "https://github.com/ajeetk095", width="stretch")

# ---------------------------------------------------------------- legal
with tab_legal:
    st.markdown(callout(DISCLAIMER, "danger"), unsafe_allow_html=True)
    st.markdown(
        "### Scope of the model\n"
        "- Prices are **risk-neutral** values of a calibrated model, not forecasts of where the stock will go.\n"
        "- The calibration uses a supplied quote sheet that is **not** arbitrage-free; part of every pricing error is "
        "therefore irreducible and is reported as an MSE floor.\n"
        "- Parameters are weakly identified. The app reports prices, confidence intervals and parameter ranges instead "
        "of presenting a single parameter vector as truth.\n"
        "- Live market data come from a free provider, are delayed and may be unavailable. Nothing on the market page "
        "feeds the calibrated results.\n\n"
        "### Licensing\n"
        "Released under the MIT licence (see `LICENSE`). Third-party references: Heston (1993), Lewis (2001), "
        "Carr & Madan (1999), Bates (1996), Andersen (2008), Cox, Ingersoll & Ross (1985)."
    )

ai_panel("About", {"bio": "Ajeet Kumar — quant finance, M.Sc. Financial Engineering (WorldQuant University)"},
         ["Why is this a strong portfolio piece?", "How would you explain this to a recruiter?"])
