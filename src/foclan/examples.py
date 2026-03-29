from __future__ import annotations

from dataclasses import dataclass

from .resources import read_json_object, read_text


@dataclass(frozen=True)
class ExampleEntry:
    name: str
    program_resource: tuple[str, ...]
    env_resource: tuple[str, ...]
    description: str

    @property
    def program_hint(self) -> str:
        return "/".join(self.program_resource)

    @property
    def env_hint(self) -> str:
        return "/".join(self.env_resource)


_EXAMPLE_MANIFEST: tuple[ExampleEntry, ...] = (
    ExampleEntry(
        name="active_top_city",
        program_resource=("examples", "current", "active_top_city.focus"),
        env_resource=("examples", "current", "env", "users_orders.json"),
        description="Keep active users and return the most common city.",
    ),
    ExampleEntry(
        name="counts_dashboard",
        program_resource=("examples", "current", "counts_dashboard.focus"),
        env_resource=("examples", "current", "env", "users_orders.json"),
        description="Return root counts for active users and paid orders.",
    ),
    ExampleEntry(
        name="choose_stats_or_meta",
        program_resource=("examples", "current", "choose_stats_or_meta.focus"),
        env_resource=("examples", "current", "env", "stats_or_meta.json"),
        description="Choose stats or metadata depending on the flag input.",
    ),
    ExampleEntry(
        name="top_user_and_paid_countries",
        program_resource=("examples", "current", "top_user_and_paid_countries.focus"),
        env_resource=("examples", "current", "env", "users_orders.json"),
        description="Return top user record and unique paid countries.",
    ),
    ExampleEntry(
        name="prepare_llm_payload",
        program_resource=("examples", "current", "prepare_llm_payload.focus"),
        env_resource=("examples", "current", "env", "llm_payload.json"),
        description="Assemble a simple provider payload object.",
    ),
)


def list_current_examples() -> tuple[ExampleEntry, ...]:
    return _EXAMPLE_MANIFEST


def get_current_example(name: str) -> ExampleEntry:
    for entry in _EXAMPLE_MANIFEST:
        if entry.name == name:
            return entry
    available = ", ".join(entry.name for entry in _EXAMPLE_MANIFEST)
    raise ValueError(f"Unknown example '{name}'. Available examples: {available}.")


def load_example_source(entry: ExampleEntry) -> str:
    return read_text(*entry.program_resource)


def load_example_env(entry: ExampleEntry) -> dict:
    return read_json_object(*entry.env_resource)
