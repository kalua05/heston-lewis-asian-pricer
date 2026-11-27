"""OpenRouter streaming client pinned to the requested free ERNIE model."""
import json
import os

import requests
import streamlit as st

URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "baidu/ernie-5.5-flash-preview:free"


def _api_key():
    try:
        key = st.secrets.get("OPENROUTER_API_KEY")
    except Exception:
        key = None
    return key or os.environ.get("OPENROUTER_API_KEY")


def stream_chat(messages, model=None):
    """Stream assistant text; model is fixed server-side, never visitor-selected."""
    key = _api_key()
    if not key:
        yield "⚠️ OPENROUTER_API_KEY is not configured in the app secrets."
        return

    try:
        with requests.post(
            URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            stream=True,
            timeout=60,
            json={"model": MODEL, "messages": messages[-9:], "stream": True, "max_tokens": 700},
        ) as response:
            if response.status_code == 401:
                yield "⚠️ The configured AI key was rejected. Check the Streamlit secret."
                return
            if response.status_code == 429:
                yield "⚠️ The AI service is rate limited; please retry shortly."
                return
            if response.status_code >= 400:
                yield "⚠️ The AI service could not complete this request. Please retry later."
                return
            for line in response.iter_lines():
                if not line or not line.startswith(b"data: ") or line == b"data: [DONE]":
                    continue
                try:
                    payload = json.loads(line[6:])
                    delta = payload["choices"][0].get("delta", {}).get("content")
                except (ValueError, KeyError, IndexError, TypeError):
                    continue
                if delta:
                    yield delta
    except requests.RequestException:
        yield "⚠️ Could not reach the AI service. Check the app connection and retry."
