from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Callable

from .ops import HostFunction


@dataclass(frozen=True)
class HostExtension:
    name: str
    description: str
    host_functions: dict[str, HostFunction]


def list_installed_extensions() -> tuple[HostExtension, ...]:
    discovered: list[HostExtension] = []
    for entry_point in entry_points(group="foclan.host_functions"):
        factory = entry_point.load()
        extension = factory()
        if not isinstance(extension, HostExtension):
            raise TypeError(
                f"Extension entry point '{entry_point.name}' must return foclan.extensions.HostExtension."
            )
        discovered.append(extension)
    discovered.sort(key=lambda item: item.name)
    return tuple(discovered)


def load_host_functions() -> dict[str, HostFunction]:
    host_functions: dict[str, HostFunction] = {}
    for extension in list_installed_extensions():
        for name, function in extension.host_functions.items():
            if name in host_functions:
                raise ValueError(f"Host function '{name}' is registered more than once.")
            host_functions[name] = function
    return host_functions

