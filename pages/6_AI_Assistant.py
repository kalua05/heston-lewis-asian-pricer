import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import *
from utils.theme import badge, callout, page_header

setup("AI Assistant", "🤖")

st.markdown(
    page_header(
        "AI assistant",
        "An optional analyst that sees the current model state and the live market snapshot. It runs on a "
        "server-selected model, never invents numbers, and is rate-limited per session.",
        kicker="Assistant",
        meta=[badge("Optional", "warn"), badge("Server-side model", "info"),
              badge("Prompt-injection guarded", "ok")],
    ),
    unsafe_allow_html=True,
)

ensure()
st.markdown(callout(DISCLAIMER, "danger"), unsafe_allow_html=True)

if not AI_ON():
    st.markdown(
        callout("The assistant is disabled because <code>OPENROUTER_API_KEY</code> is not configured. "
                "Copy <code>.streamlit/secrets.toml.example</code> to <code>.streamlit/secrets.toml</code> and add "
                "your key — or set the environment variable. No other part of the app needs a key.",
                "warn", "Offline"),
        unsafe_allow_html=True,
    )
    st.markdown(
        "##### What the assistant would add\n"
        "- Plain-language narration of the current calibration and price.\n"
        "- Separate framing for a retail client, a professional investor and a corporate treasurer.\n"
        "- A quick check-list of what would invalidate a recommendation.\n"
    )
    st.stop()

ss.setdefault("chat", [])

with st.container(border=True):
    st.markdown("#### Context the assistant can see")
    c = st.columns(4)
    c[0].metric("Heston v₀", f"{ss.p[0]:.3f}")
    c[1].metric("κ / θ", f"{ss.p[1]:.2f} / {ss.p[2]:.3f}")
    c[2].metric("σ / ρ", f"{ss.p[3]:.2f} / {ss.p[4]:.2f}")
    live = ss.get("home_live") or {}
    c[3].metric("SM spot (live)", money(live.get("spot"), 2) if live.get("spot") else DASH)

suggestions = [
    "Analyse the current market and model situation",
    "Recommendations for a retail investor",
    "Recommendations for a corporate treasury",
    "Recommendations for a professional investor",
    "Explain the main risks and data limitations",
]
chosen = st.pills("Suggested prompts", suggestions, selection_mode="single", key="ai_pills")

for message in ss.chat:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask about the model, the market or the risks")
if chosen and not question:
    question = chosen

if question:
    ok, why = ai_allowed()
    if not ok:
        st.warning(why)
    else:
        question = clip(question, MAX_AI_CHARS)
        ss.chat.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        ctx = base_context("AI Assistant", {"live": ss.get("home_live")})
        messages = [{"role": "system", "content": SYS + f"\nAPP STATE: {ctx}\nLIVE DATA: {live_ctx()}"}] + ss.chat[-8:]
        with st.chat_message("assistant"):
            answer = st.write_stream(orc.stream_chat(messages))
        ss.chat.append({"role": "assistant", "content": answer})

if ss.chat:
    c = st.columns([1, 4])
    if c[0].button("Clear conversation", width="stretch"):
        ss.chat = []
        st.rerun()
    c[1].markdown(caption("Conversation is held in this browser session only — nothing is persisted server-side."),
                  unsafe_allow_html=True)
