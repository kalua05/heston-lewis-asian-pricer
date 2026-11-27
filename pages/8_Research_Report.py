import io
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import *
from utils.theme import badge, callout, empty_state, kpi_row, page_header

setup("Report & Downloads", "📄")

st.markdown(
    page_header(
        "Report, notebook and downloads",
        "The deliverables the brief asks for — an answers-only PDF, an executable notebook with its HTML export, "
        "and the supporting audit material — plus a machine-readable export of every number in the app.",
        kicker="Assignment",
        meta=[badge("PDF · no code", "info"), badge("Notebook + HTML", "info"), badge("Audit log", "neutral")],
    ),
    unsafe_allow_html=True,
)

pdf = REPORT_DIR / "GWP1_report.pdf"
nb = NOTEBOOK_DIR / "GWP1_notebook.ipynb"
html = NOTEBOOK_DIR / "GWP1_notebook.html"
brief = REPORT_DIR / "assignment_brief.pdf"
lewis = REPORT_DIR / "lewis_2001.pdf"

R_ = get_results()
M = R_["meta"]

# ---------------------------------------------------------------- deliverables
st.markdown("## Deliverables")
cols = st.columns(3, gap="medium")
with cols[0]:
    with st.container(border=True):
        st.markdown("#### 📄 Report")
        st.markdown("<div class='gsq-cap'>Answers only, no code, with technical and non-technical sections "
                    "and MLA references.</div>", unsafe_allow_html=True)
        if pdf.exists():
            st.download_button("⬇ PDF", pdf.read_bytes(), pdf.name, "application/pdf", key="dl_pdf", width="stretch")
            st.markdown(caption(f"{pdf.stat().st_size / 1e6:.1f} MB"), unsafe_allow_html=True)
        else:
            st.markdown(callout("Report file not found in <code>reports/</code>.", "warn"), unsafe_allow_html=True)
with cols[1]:
    with st.container(border=True):
        st.markdown("#### 📓 Notebook")
        st.markdown("<div class='gsq-cap'>Self-contained, executed notebook with the HTML export in one zip.</div>",
                    unsafe_allow_html=True)
        if nb.exists() and html.exists():
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                z.write(nb, nb.name)
                z.write(html, html.name)
            st.download_button("⬇ Notebook zip", buf.getvalue(), "GWP1_notebook_and_html.zip", "application/zip",
                               key="dl_nb", width="stretch")
            st.markdown(caption(f"{nb.stat().st_size / 1e6:.1f} MB notebook + {html.stat().st_size / 1e6:.1f} MB HTML"),
                        unsafe_allow_html=True)
        else:
            st.markdown(callout("Notebook artefacts missing — rebuild with <code>python build_notebook.py</code>.", "warn"),
                        unsafe_allow_html=True)
with cols[2]:
    with st.container(border=True):
        st.markdown("#### 📊 Results export")
        st.markdown("<div class='gsq-cap'>Every parameter, fit statistic and scenario percentile as CSV and Excel.</div>",
                    unsafe_allow_html=True)
        sheets = {
            "Summary": pd.DataFrame([
                {"Key": "spot", "Value": M["spot"]}, {"Key": "rate", "Value": M["r"]},
                {"Key": "fee", "Value": M["fee"]}, {"Key": "n_mc", "Value": M["n_mc"]},
                {"Key": "generated", "Value": M["generated"]},
                {"Key": "Asian 20d fair", "Value": R_["step1c"]["qe"]["price"]},
                {"Key": "Asian 20d client", "Value": R_["step1c"]["qe"]["client"]},
                {"Key": "Put 70d fair", "Value": R_["step2c"]["models"][R_["step2c"]["headline"]]["mc"]["price"]},
                {"Key": "E[12M Euribor 1y]", "Value": R_["step3b"]["expected"]},
            ]),
            "Step1a": pd.DataFrame([R_["step1a"]["params"]]),
            "Step1b": pd.DataFrame([R_["step1b"]["params"]]),
            "Step2a": pd.DataFrame([R_["step2a"]["params"]]),
            "Step2b": pd.DataFrame([R_["step2b"]["params"]]),
            "Put70d": pd.DataFrame([{"model": k, "mc": v["mc"]["price"], "fourier": v["fourier"], "z": v["z"]}
                                    for k, v in R_["step2c"]["models"].items()]),
            "Euribor": pd.DataFrame(R_["step3b"]["sigma_sensitivity"]),
        }
        export_row(sheets["Summary"], "gwp1_results", "rep_export", excel=sheets)

# ---------------------------------------------------------------- readers
st.markdown("## Read the material")
tabs = st.tabs(["Report (PDF)", "Notebook (HTML)", "Assignment brief", "Lewis (2001)", "Corrections & audit"])

with tabs[0]:
    if pdf.exists():
        st.markdown(
            callout("The PDF opens inline where the browser supports it; otherwise use the download button above.",
                    "info"),
            unsafe_allow_html=True,
        )
        pdf_view(pdf, 760, key="pdf_report")
    else:
        st.markdown(empty_state("Report not found", "Place GWP1_report.pdf in the reports/ folder."), unsafe_allow_html=True)

with tabs[1]:
    if html.exists():
        st.iframe(str(html), height=800)
    else:
        st.markdown(empty_state("HTML export not found", "Run the notebook export step in the README."), unsafe_allow_html=True)

with tabs[2]:
    if brief.exists():
        pdf_view(brief, 700, key="pdf_brief")
    else:
        st.markdown(empty_state("Brief not found", "The assignment brief is not bundled with this copy."), unsafe_allow_html=True)

with tabs[3]:
    if lewis.exists():
        pdf_view(lewis, 700, key="pdf_lewis")
    else:
        st.markdown(empty_state("Reference not found", "Lewis (2001) is not bundled with this copy."), unsafe_allow_html=True)

with tabs[4]:
    corrections = DOC_DIR / "CORRECTIONS.md"
    if corrections.exists():
        st.markdown(corrections.read_text())
    else:
        st.markdown(empty_state("Audit log missing", "documentation/CORRECTIONS.md was not found."), unsafe_allow_html=True)

ai_panel("Report", {"note": "Lewis (2001): C = S - sqrt(SK)e^{-rT}/pi * ∫ Re[e^{iuk} φ(u-i/2)]/(u²+1/4) du"},
         ["Summarise Lewis (2001) in five bullets", "What are the main limitations of this project?"])
