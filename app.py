"""Navigation entrypoint for the SM Energy Pricer (MScFE 622 GWP1).

Pages are grouped into five sections so the sidebar reads like a product rather
than a file list.  ``st.navigation`` hands routing, deep links and the browser
back/forward stack to Streamlit.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from utils.theme import CSS

st.set_page_config(page_title="SM Energy Pricer · MScFE 622 GWP1", page_icon="📈", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


def page(filename: str, title: str, icon: str, default: bool = False):
    slug = filename.split("_", 1)[1][:-3].lower().replace("_", "-")
    return st.Page(f"pages/{filename}", title=title, icon=icon, url_path=slug, default=default)


nav = st.navigation(
    {
        "Overview": [
            page("0_Home.py", "Dashboard", "🏠", default=True),
            page("5_Real_Time_Data.py", "Market Data", "📡"),
        ],
        "Analysis": [
            page("1_Live_Simulation.py", "Pricing Workbench", "📈"),
            page("3_Model_Diagnostics.py", "Model Diagnostics", "🔍"),
            page("4_Recommendations.py", "Recommendations", "💡"),
        ],
        "Assignment": [
            page("2_Assignment_Tasks.py", "Assignment Tasks", "📝"),
            page("8_Research_Report.py", "Report & Downloads", "📄"),
            page("9_Presentation.py", "Presentation", "🎞️"),
        ],
        "Assistant": [
            page("6_AI_Assistant.py", "AI Assistant", "🤖"),
        ],
        "Reference": [
            page("7_Learn.py", "Learn the Model", "🎓"),
            page("10_About.py", "About & Docs", "ℹ️"),
            page("14_Roadmap.py", "Roadmap", "🧭"),
        ],
    }
)
nav.run()
