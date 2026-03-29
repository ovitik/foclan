from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from importlib.resources import files


PACKAGE_RESOURCES = files("foclan").joinpath("resources")


def read_text(*parts: str) -> str:
    return PACKAGE_RESOURCES.joinpath(*parts).read_text(encoding="utf-8")


def read_json_object(*parts: str) -> dict[str, Any]:
    data = json.loads(read_text(*parts))
    if not isinstance(data, dict):
        joined = "/".join(parts)
        raise ValueError(f"Resource {joined} must contain a JSON object.")
    return data


def write_text_resource(target: Path, parts: tuple[str, ...], force: bool = False) -> Path:
    if target.exists() and not force:
        raise FileExistsError(f"{target} already exists. Use --force to overwrite it.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(read_text(*parts), encoding="utf-8")
    return target
