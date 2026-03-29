from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .resources import write_text_resource


@dataclass(frozen=True)
class ScaffoldTarget:
    name: str
    relative_path: Path
    resource_parts: tuple[str, ...]


CODEX_TARGET = ScaffoldTarget(
    name="codex",
    relative_path=Path("AGENTS.md"),
    resource_parts=("templates", "codex", "AGENTS.md"),
)

CURSOR_TARGET = ScaffoldTarget(
    name="cursor",
    relative_path=Path(".cursor") / "rules" / "foclan-v1.mdc",
    resource_parts=("templates", "cursor", "foclan-v1.mdc"),
)


def scaffold_targets(kind: str) -> tuple[ScaffoldTarget, ...]:
    if kind == "codex":
        return (CODEX_TARGET,)
    if kind == "cursor":
        return (CURSOR_TARGET,)
    if kind == "all":
        return (CODEX_TARGET, CURSOR_TARGET)
    raise ValueError(f"Unsupported scaffold kind '{kind}'.")


def write_scaffold(kind: str, project_dir: Path, force: bool = False) -> list[Path]:
    written: list[Path] = []
    for target in scaffold_targets(kind):
        path = project_dir / target.relative_path
        write_text_resource(path, target.resource_parts, force=force)
        written.append(path)
    return written
