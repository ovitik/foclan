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

PROJECT_README_TARGET = ScaffoldTarget(
    name="project-readme",
    relative_path=Path("README.md"),
    resource_parts=("templates", "project", "README.md"),
)

PROJECT_GITIGNORE_TARGET = ScaffoldTarget(
    name="project-gitignore",
    relative_path=Path(".gitignore"),
    resource_parts=("templates", "project", "gitignore.txt"),
)

PROJECT_ENV_EXAMPLE_TARGET = ScaffoldTarget(
    name="project-env-example",
    relative_path=Path(".env.example"),
    resource_parts=("templates", "project", "env.example"),
)

PROJECT_COUNTS_PROGRAM_TARGET = ScaffoldTarget(
    name="project-counts-program",
    relative_path=Path("programs") / "counts_dashboard.focus",
    resource_parts=("templates", "project", "programs", "counts_dashboard.focus"),
)

PROJECT_LLM_PROGRAM_TARGET = ScaffoldTarget(
    name="project-llm-program",
    relative_path=Path("programs") / "extract_contact.focus",
    resource_parts=("templates", "project", "programs", "extract_contact.focus"),
)

PROJECT_USERS_ORDERS_INPUT_TARGET = ScaffoldTarget(
    name="project-users-orders-input",
    relative_path=Path("inputs") / "users_orders.json",
    resource_parts=("templates", "project", "inputs", "users_orders.json"),
)

PROJECT_CONTACT_INPUT_TARGET = ScaffoldTarget(
    name="project-contact-input",
    relative_path=Path("inputs") / "contact_extract.json",
    resource_parts=("templates", "project", "inputs", "contact_extract.json"),
)


def scaffold_targets(kind: str) -> tuple[ScaffoldTarget, ...]:
    if kind == "codex":
        return (CODEX_TARGET,)
    if kind == "cursor":
        return (CURSOR_TARGET,)
    if kind == "all":
        return (CODEX_TARGET, CURSOR_TARGET)
    if kind == "project":
        return (
            PROJECT_README_TARGET,
            PROJECT_GITIGNORE_TARGET,
            PROJECT_ENV_EXAMPLE_TARGET,
            PROJECT_COUNTS_PROGRAM_TARGET,
            PROJECT_LLM_PROGRAM_TARGET,
            PROJECT_USERS_ORDERS_INPUT_TARGET,
            PROJECT_CONTACT_INPUT_TARGET,
            CODEX_TARGET,
            CURSOR_TARGET,
        )
    raise ValueError(f"Unsupported scaffold kind '{kind}'.")


def write_scaffold(kind: str, project_dir: Path, force: bool = False) -> list[Path]:
    written: list[Path] = []
    for target in scaffold_targets(kind):
        path = project_dir / target.relative_path
        write_text_resource(path, target.resource_parts, force=force)
        written.append(path)
    return written
