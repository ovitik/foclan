from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import httpx

from foclan.extensions import HostExtension


OPENAI_URL = "https://api.openai.com/v1/responses"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
GOOGLE_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
ANTHROPIC_VERSION = "2023-06-01"


class LLMConfigError(ValueError):
    pass


class LLMProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMRequest:
    provider: str
    model: str
    input_text: str
    system: str | None
    temperature: float | None
    max_output_tokens: int | None
    timeout_seconds: float
    schema: dict[str, Any] | None
    schema_name: str


def register_host_functions() -> HostExtension:
    return HostExtension(
        name="foclan-llm",
        description="Load .env-backed API keys and call OpenAI, Anthropic, and Google LLM APIs.",
        host_functions={
            "llm_text": llm_text,
            "llm_json": llm_json,
        },
    )


def llm_text(focus: Any, *args: Any) -> str:
    if args:
        raise LLMConfigError("llm_text does not accept positional arguments.")
    request = _normalize_request(focus, require_schema=False)
    if request.provider == "openai":
        return _openai_text(request)
    if request.provider == "anthropic":
        return _anthropic_text(request)
    if request.provider == "google":
        return _google_text(request)
    raise LLMConfigError(f"Unsupported provider '{request.provider}'.")


def llm_json(focus: Any, *args: Any) -> Any:
    if args:
        raise LLMConfigError("llm_json does not accept positional arguments.")
    request = _normalize_request(focus, require_schema=True)
    if request.provider == "openai":
        return _openai_json(request)
    if request.provider == "anthropic":
        return _anthropic_json(request)
    if request.provider == "google":
        return _google_json(request)
    raise LLMConfigError(f"Unsupported provider '{request.provider}'.")


def _normalize_request(focus: Any, require_schema: bool) -> LLMRequest:
    if not isinstance(focus, dict):
        raise LLMConfigError("llm_text/llm_json expect a record focus.")

    provider = str(focus.get("provider", "")).strip().lower()
    model = str(focus.get("model", "")).strip()
    if not provider:
        raise LLMConfigError("LLM request must include 'provider'.")
    if provider == "gemini":
        provider = "google"
    if not model:
        raise LLMConfigError("LLM request must include 'model'.")
    if "input" not in focus:
        raise LLMConfigError("LLM request must include 'input'.")

    schema = focus.get("schema")
    if require_schema:
        if not isinstance(schema, dict):
            raise LLMConfigError("llm_json requires 'schema' to be a JSON Schema object.")
    else:
        schema = None

    temperature = focus.get("temperature")
    if temperature is not None:
        temperature = float(temperature)

    max_output_tokens = focus.get("max_output_tokens")
    if max_output_tokens is not None:
        max_output_tokens = int(max_output_tokens)

    timeout_seconds = float(focus.get("timeout_seconds", 60.0))
    schema_name = str(focus.get("schema_name", "foclan_response"))

    return LLMRequest(
        provider=provider,
        model=model,
        input_text=_stringify_input(focus["input"]),
        system=str(focus["system"]) if focus.get("system") is not None else None,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        timeout_seconds=timeout_seconds,
        schema=schema,
        schema_name=schema_name,
    )


def _stringify_input(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _openai_text(request: LLMRequest) -> str:
    body: dict[str, Any] = {
        "model": request.model,
        "input": request.input_text,
    }
    if request.system:
        body["instructions"] = request.system
    if request.temperature is not None:
        body["temperature"] = request.temperature
    if request.max_output_tokens is not None:
        body["max_output_tokens"] = request.max_output_tokens

    response = _post_json(
        OPENAI_URL,
        headers={
            "Authorization": f"Bearer {_require_env('OPENAI_API_KEY')}",
            "Content-Type": "application/json",
        },
        body=body,
        timeout_seconds=request.timeout_seconds,
    )
    return _extract_openai_text(response)


def _openai_json(request: LLMRequest) -> Any:
    assert request.schema is not None
    body: dict[str, Any] = {
        "model": request.model,
        "input": request.input_text,
        "text": {
            "format": {
                "type": "json_schema",
                "name": request.schema_name,
                "strict": True,
                "schema": request.schema,
            }
        },
    }
    if request.system:
        body["instructions"] = request.system
    if request.temperature is not None:
        body["temperature"] = request.temperature
    if request.max_output_tokens is not None:
        body["max_output_tokens"] = request.max_output_tokens

    response = _post_json(
        OPENAI_URL,
        headers={
            "Authorization": f"Bearer {_require_env('OPENAI_API_KEY')}",
            "Content-Type": "application/json",
        },
        body=body,
        timeout_seconds=request.timeout_seconds,
    )
    return _parse_json_text(_extract_openai_text(response), provider="openai")


def _anthropic_text(request: LLMRequest) -> str:
    body: dict[str, Any] = {
        "model": request.model,
        "max_tokens": request.max_output_tokens or 1024,
        "messages": [{"role": "user", "content": request.input_text}],
    }
    if request.system:
        body["system"] = request.system
    if request.temperature is not None:
        body["temperature"] = request.temperature

    response = _post_json(
        ANTHROPIC_URL,
        headers={
            "x-api-key": _require_env("ANTHROPIC_API_KEY"),
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        body=body,
        timeout_seconds=request.timeout_seconds,
    )
    return _extract_anthropic_text(response)


def _anthropic_json(request: LLMRequest) -> Any:
    assert request.schema is not None
    body: dict[str, Any] = {
        "model": request.model,
        "max_tokens": request.max_output_tokens or 1024,
        "messages": [{"role": "user", "content": request.input_text}],
        "tools": [
            {
                "name": "emit_json",
                "description": "Return the final structured JSON result.",
                "input_schema": request.schema,
            }
        ],
        "tool_choice": {"type": "tool", "name": "emit_json"},
    }
    if request.system:
        body["system"] = request.system
    if request.temperature is not None:
        body["temperature"] = request.temperature

    response = _post_json(
        ANTHROPIC_URL,
        headers={
            "x-api-key": _require_env("ANTHROPIC_API_KEY"),
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        body=body,
        timeout_seconds=request.timeout_seconds,
    )
    return _extract_anthropic_tool_input(response)


def _google_text(request: LLMRequest) -> str:
    body = _build_google_body(request)
    response = _post_json(
        GOOGLE_URL_TEMPLATE.format(model=request.model),
        headers={
            "x-goog-api-key": _require_env("GEMINI_API_KEY", "GOOGLE_API_KEY"),
            "Content-Type": "application/json",
        },
        body=body,
        timeout_seconds=request.timeout_seconds,
    )
    return _extract_google_text(response)


def _google_json(request: LLMRequest) -> Any:
    assert request.schema is not None
    body = _build_google_body(request)
    generation_config = body.setdefault("generationConfig", {})
    generation_config["responseMimeType"] = "application/json"
    generation_config["responseJsonSchema"] = request.schema

    response = _post_json(
        GOOGLE_URL_TEMPLATE.format(model=request.model),
        headers={
            "x-goog-api-key": _require_env("GEMINI_API_KEY", "GOOGLE_API_KEY"),
            "Content-Type": "application/json",
        },
        body=body,
        timeout_seconds=request.timeout_seconds,
    )
    return _parse_json_text(_extract_google_text(response), provider="google")


def _build_google_body(request: LLMRequest) -> dict[str, Any]:
    body: dict[str, Any] = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": request.input_text}],
            }
        ]
    }
    if request.system:
        body["systemInstruction"] = {"parts": [{"text": request.system}]}
    generation_config: dict[str, Any] = {}
    if request.temperature is not None:
        generation_config["temperature"] = request.temperature
    if request.max_output_tokens is not None:
        generation_config["maxOutputTokens"] = request.max_output_tokens
    if generation_config:
        body["generationConfig"] = generation_config
    return body


def _extract_openai_text(response: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    if chunks:
        return "".join(chunks).strip()
    raise LLMProviderError("OpenAI response did not contain output text.")


def _extract_anthropic_text(response: dict[str, Any]) -> str:
    chunks = [
        block["text"]
        for block in response.get("content", [])
        if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str)
    ]
    if chunks:
        return "".join(chunks).strip()
    raise LLMProviderError("Anthropic response did not contain text content.")


def _extract_anthropic_tool_input(response: dict[str, Any]) -> Any:
    for block in response.get("content", []):
        if isinstance(block, dict) and block.get("type") == "tool_use" and "input" in block:
            return block["input"]
    raise LLMProviderError("Anthropic response did not contain a tool_use block.")


def _extract_google_text(response: dict[str, Any]) -> str:
    chunks: list[str] = []
    for candidate in response.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content")
        if not isinstance(content, dict):
            continue
        for part in content.get("parts", []):
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                chunks.append(part["text"])
    if chunks:
        return "".join(chunks).strip()
    raise LLMProviderError("Google response did not contain text content.")


def _parse_json_text(text: str, provider: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMProviderError(f"{provider} did not return valid JSON.") from exc


def _require_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    joined = " or ".join(names)
    raise LLMConfigError(f"Missing required API key in environment: {joined}.")


def _post_json(url: str, headers: dict[str, str], body: dict[str, Any], timeout_seconds: float) -> dict[str, Any]:
    response = httpx.post(url, headers=headers, json=body, timeout=timeout_seconds)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise LLMProviderError(f"Provider call failed: {exc.response.text}") from exc
    data = response.json()
    if not isinstance(data, dict):
        raise LLMProviderError("Provider response must be a JSON object.")
    return data
