import os

import pytest

from foclan.extensions import HostExtension
from foclan_llm import register_host_functions
from foclan_llm import providers


def test_register_host_functions_returns_extension() -> None:
    extension = register_host_functions()
    assert isinstance(extension, HostExtension)
    assert extension.name == "foclan-llm"
    assert sorted(extension.host_functions) == ["llm_json", "llm_text"]


def test_openai_text_uses_responses_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    captured: dict[str, object] = {}

    def fake_post_json(url: str, headers: dict[str, str], body: dict[str, object], timeout_seconds: float) -> dict[str, object]:
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = body
        captured["timeout"] = timeout_seconds
        return {
            "output": [
                {
                    "content": [
                        {"type": "output_text", "text": "hello world"},
                    ]
                }
            ]
        }

    monkeypatch.setattr(providers, "_post_json", fake_post_json)
    text = providers.llm_text(
        {
            "provider": "openai",
            "model": "gpt-5-mini",
            "input": {"message": "hi"},
            "system": "be brief",
            "max_output_tokens": 50,
        }
    )

    assert text == "hello world"
    assert captured["url"] == providers.OPENAI_URL
    assert "Authorization" in captured["headers"]  # type: ignore[index]
    assert (captured["body"])["model"] == "gpt-5-mini"  # type: ignore[index]


def test_anthropic_json_uses_tool_for_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def fake_post_json(url: str, headers: dict[str, str], body: dict[str, object], timeout_seconds: float) -> dict[str, object]:
        assert url == providers.ANTHROPIC_URL
        assert headers["anthropic-version"] == providers.ANTHROPIC_VERSION
        tools = body["tools"]  # type: ignore[index]
        assert isinstance(tools, list) and tools[0]["name"] == "emit_json"
        return {"content": [{"type": "tool_use", "input": {"name": "Jane", "age": 54}}]}

    monkeypatch.setattr(providers, "_post_json", fake_post_json)
    value = providers.llm_json(
        {
            "provider": "anthropic",
            "model": "claude-sonnet-4-5",
            "input": "Jane is 54.",
            "schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
                "required": ["name", "age"],
                "additionalProperties": False,
            },
        }
    )

    assert value == {"name": "Jane", "age": 54}


def test_google_json_uses_structured_output_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    def fake_post_json(url: str, headers: dict[str, str], body: dict[str, object], timeout_seconds: float) -> dict[str, object]:
        assert ":generateContent" in url
        assert headers["x-goog-api-key"] == "test-key"
        generation_config = body["generationConfig"]  # type: ignore[index]
        assert generation_config["responseMimeType"] == "application/json"
        assert "responseJsonSchema" in generation_config
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": '{"answer":"ok"}'}],
                    }
                }
            ]
        }

    monkeypatch.setattr(providers, "_post_json", fake_post_json)
    value = providers.llm_json(
        {
            "provider": "google",
            "model": "gemini-2.5-flash",
            "input": "Return {\"answer\":\"ok\"}.",
            "schema": {
                "type": "object",
                "properties": {"answer": {"type": "string"}},
                "required": ["answer"],
                "additionalProperties": False,
            },
        }
    )

    assert value == {"answer": "ok"}


def test_missing_schema_for_llm_json_raises() -> None:
    with pytest.raises(providers.LLMConfigError, match="requires 'schema'"):
        providers.llm_json({"provider": "openai", "model": "gpt-5-mini", "input": "hello"})


def test_require_env_raises_for_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(providers.LLMConfigError, match="OPENAI_API_KEY"):
        providers._require_env("OPENAI_API_KEY")


def test_openai_incomplete_error_mentions_max_output_tokens() -> None:
    with pytest.raises(providers.LLMProviderError, match="max_output_tokens"):
        providers._extract_openai_text(
            {
                "status": "incomplete",
                "incomplete_details": {"reason": "max_output_tokens"},
                "output": [],
            }
        )


def test_google_max_tokens_error_is_clear() -> None:
    with pytest.raises(providers.LLMProviderError, match="MAX_TOKENS"):
        providers._extract_google_text({"candidates": [{"finishReason": "MAX_TOKENS"}]})
