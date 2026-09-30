from types import SimpleNamespace

import pytest

import mopk.devbench.client as transport
from mopk.devbench import Client, DevBenchError


def test_tool_errors_raise_and_keep_the_receipt(monkeypatch):
    result = {
        "content": [{"type": "text", "text": "No preview is visible"}],
        "isError": True,
    }
    session = SimpleNamespace(
        headers={},
        post=lambda url, *, json, timeout: SimpleNamespace(
            ok=True, json=lambda: result
        ),
    )
    monkeypatch.setattr(transport.requests, "Session", lambda: session)
    client = Client("http://127.0.0.1:8930", session="abc")

    with pytest.raises(
        DevBenchError, match="preview_nif failed: No preview is visible"
    ):
        client.call("preview_nif", {"action": "inspect"})

    assert session.headers["X-Dev-Bench-Session"] == "abc"
    assert client.transcript[0]["result"] == result
    assert "No preview is visible" in client.transcript[0]["error"]
