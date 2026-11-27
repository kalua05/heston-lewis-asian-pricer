import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import *
from ppt.make_deck import build, slides
from utils.theme import badge, callout, page_header


setup("Presentation", "🎞️")

st.markdown(
    page_header(
        "Presentation",
        "A ten-slide walkthrough generated from the same results file as the report and the app, so the deck can "
        "never drift out of sync with the numbers.",
        kicker="Assignment",
        meta=[badge("10 slides", "info"), badge("Generated from results JSON", "ok")],
    ),
    unsafe_allow_html=True,
)

R_ = get_results()

with guard("Deck build"):
    path = build(R_)
    data = open(path, "rb").read()

c = st.columns([1, 2])
with c[0]:
    st.download_button("⬇ PowerPoint deck", data, "gwp1_deck.pptx",
                       "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                       key="dl_deck", width="stretch")
with c[1]:
    st.markdown(
        callout("The deck is rebuilt on every page load directly from <code>results/gwp1_results.json</code>. "
                "Re-run the pipeline and the slides update themselves — there are no hard-coded numbers in the template.",
                "info"),
        unsafe_allow_html=True,
    )

st.markdown("## Slide script")
for i, (title, body) in enumerate(slides(R_), start=1):
    with st.container(border=True):
        st.markdown(f"**Slide {i} — {title}**")
        for line in body.split("\n"):
            st.markdown(f"<div class='gsq-cap' style='font-size:.86rem'>{esc(line)}</div>", unsafe_allow_html=True)

ai_panel("Presentation", None, ["Give me a 60-second pitch of this project",
                                "Which questions will an examiner ask?"])
