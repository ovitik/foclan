import httpx
import pytest

from foclan.extensions import HostExtension
from foclan_http import register_host_functions
from foclan_http import http_ops


def test_register_host_functions_returns_extension() -> None:
    extension = register_host_functions()
    assert isinstance(extension, HostExtension)
    assert extension.name == "foclan-http"
    assert "http_get_json" in extension.host_functions


def test_http_get_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url, headers=None, params=None, timeout=None):
        return httpx.Response(200, request=httpx.Request("GET", url), json={"ok": True})

    monkeypatch.setattr(http_ops.httpx, "get", fake_get)
    assert http_ops.http_get_json({"url": "https://example.com"}) == {"ok": True}


def test_http_post_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url, headers=None, params=None, json=None, timeout=None):
        return httpx.Response(200, request=httpx.Request("POST", url), json={"echo": json})

    monkeypatch.setattr(http_ops.httpx, "post", fake_post)
    value = http_ops.http_post_json({"url": "https://example.com", "json": {"x": 1}})
    assert value == {"echo": {"x": 1}}


def test_env_backed_header_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_TOKEN", "secret")
    headers = http_ops._resolve_headers({"Authorization": {"env": "API_TOKEN", "prefix": "Bearer "}})
    assert headers == {"Authorization": "Bearer secret"}
