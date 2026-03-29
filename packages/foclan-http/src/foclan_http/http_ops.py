from __future__ import annotations

import json
import os
from typing import Any

import httpx

from foclan.extensions import HostExtension


class HTTPConfigError(ValueError):
    pass


class HTTPRequestError(RuntimeError):
    pass


def register_host_functions() -> HostExtension:
    return HostExtension(
        name="foclan-http",
        description="Make simple deterministic HTTP GET and POST calls from Foclan.",
        host_functions={
            "http_get_json": http_get_json,
            "http_get_text": http_get_text,
            "http_post_json": http_post_json,
        },
    )


def http_get_json(focus: Any, *args: Any) -> Any:
    _reject_args("http_get_json", args)
    request = _normalize_request(focus)
    response = httpx.get(
        _require_url(request),
        headers=_resolve_headers(request.get("headers")),
        params=_resolve_params(request.get("params")),
        timeout=float(request.get("timeout_seconds", 30.0)),
    )
    _raise_for_status(response)
    return response.json()


def http_get_text(focus: Any, *args: Any) -> str:
    _reject_args("http_get_text", args)
    request = _normalize_request(focus)
    response = httpx.get(
        _require_url(request),
        headers=_resolve_headers(request.get("headers")),
        params=_resolve_params(request.get("params")),
        timeout=float(request.get("timeout_seconds", 30.0)),
    )
    _raise_for_status(response)
    return response.text


def http_post_json(focus: Any, *args: Any) -> Any:
    _reject_args("http_post_json", args)
    request = _normalize_request(focus)
    response = httpx.post(
        _require_url(request),
        headers=_resolve_headers(request.get("headers")),
        params=_resolve_params(request.get("params")),
        json=request.get("json"),
        timeout=float(request.get("timeout_seconds", 30.0)),
    )
    _raise_for_status(response)
    return response.json()


def _normalize_request(focus: Any) -> dict[str, Any]:
    if not isinstance(focus, dict):
        raise HTTPConfigError("foclan-http host functions expect a record focus.")
    return focus


def _require_url(request: dict[str, Any]) -> str:
    url = request.get("url")
    if not isinstance(url, str) or not url.strip():
        raise HTTPConfigError("HTTP request must include non-empty string 'url'.")
    return url


def _resolve_headers(value: Any) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise HTTPConfigError("'headers' must be a record.")
    headers: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise HTTPConfigError("Header names must be strings.")
        headers[key] = _resolve_header_value(item)
    return headers


def _resolve_header_value(value: Any) -> str:
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        env_name = value.get("env")
        prefix = str(value.get("prefix", ""))
        if not isinstance(env_name, str) or not env_name.strip():
            raise HTTPConfigError("Environment-backed header values require non-empty string 'env'.")
        env_value = os.getenv(env_name)
        if not env_value:
            raise HTTPConfigError(f"Missing required environment variable '{env_name}' for HTTP header.")
        return prefix + env_value
    raise HTTPConfigError("Header values must be plain scalars or {'env': ..., 'prefix': ...} records.")


def _resolve_params(value: Any) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise HTTPConfigError("'params' must be a record.")
    params: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise HTTPConfigError("Query parameter names must be strings.")
        if isinstance(item, (str, int, float, bool)):
            params[key] = str(item)
        else:
            params[key] = json.dumps(item, ensure_ascii=False)
    return params


def _raise_for_status(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPRequestError(f"HTTP call failed: {exc.response.status_code} {exc.response.text}") from exc


def _reject_args(name: str, args: tuple[Any, ...]) -> None:
    if args:
        raise HTTPConfigError(f"{name} does not accept positional arguments.")
