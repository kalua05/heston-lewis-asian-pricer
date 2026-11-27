from api import openrouter_client as client


def test_stream_chat_uses_server_selected_ernie_model(monkeypatch):
    captured = {}

    class Response:
        status_code = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def iter_lines(self):
            yield b'data: {"choices":[{"delta":{"content":"Hello"}}]}'
            yield b"data: [DONE]"

    def fake_post(*args, **kwargs):
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(client, "_api_key", lambda: "test-key")
    monkeypatch.setattr(client.requests, "post", fake_post)
    assert "".join(client.stream_chat([{"role": "user", "content": "Hi"}], "untrusted/visitor-model")) == "Hello"
    assert captured["json"]["model"] == "baidu/ernie-5.5-flash-preview:free"


def test_stream_chat_reports_missing_key(monkeypatch):
    monkeypatch.setattr(client, "_api_key", lambda: None)
    assert list(client.stream_chat([])) == ["⚠️ OPENROUTER_API_KEY is not configured in the app secrets."]
