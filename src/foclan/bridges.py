from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Any, Callable


BridgeHandler = Callable[[str, Any, "BridgeExecutionPolicy"], Any]


@dataclass(frozen=True)
class BridgeExecutionPolicy:
    timeout_seconds: float = 1.0
    allow_imports: bool = False
    allow_filesystem: bool = False
    allow_network: bool = False


@dataclass(frozen=True)
class BridgeRuntime:
    name: str
    description: str
    handler: BridgeHandler
    default_policy: BridgeExecutionPolicy = BridgeExecutionPolicy()


def list_installed_bridge_runtimes() -> tuple[BridgeRuntime, ...]:
    discovered: list[BridgeRuntime] = []
    for entry_point in entry_points(group="foclan.bridge_runtimes"):
        factory = entry_point.load()
        runtime = factory()
        if not isinstance(runtime, BridgeRuntime):
            raise TypeError(
                f"Bridge entry point '{entry_point.name}' must return foclan.bridges.BridgeRuntime."
            )
        discovered.append(runtime)
    discovered.sort(key=lambda item: item.name)
    return tuple(discovered)


def load_bridge_runtimes() -> dict[str, BridgeRuntime]:
    runtimes: dict[str, BridgeRuntime] = {}
    for runtime in list_installed_bridge_runtimes():
        if runtime.name in runtimes:
            raise ValueError(f"Bridge runtime '{runtime.name}' is registered more than once.")
        runtimes[runtime.name] = runtime
    return runtimes
