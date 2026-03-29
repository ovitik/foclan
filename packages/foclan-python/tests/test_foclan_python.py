from __future__ import annotations

import pytest

from foclan.bridges import BridgeExecutionPolicy
from foclan_python.bridge import PythonBridgeError, register_bridge_runtime, run_python_bridge


def test_register_bridge_runtime_returns_python_runtime() -> None:
    runtime = register_bridge_runtime()
    assert runtime.name == "python"
    assert runtime.default_policy.timeout_seconds == 1.0


def test_run_python_bridge_transforms_focus() -> None:
    result = run_python_bridge(
        'result = [item["name"] for item in focus if item.get("active")]',
        [{"name": "A", "active": True}, {"name": "B", "active": False}],
        BridgeExecutionPolicy(timeout_seconds=1.0),
    )
    assert result == ["A"]


def test_run_python_bridge_rejects_imports() -> None:
    with pytest.raises(PythonBridgeError, match="disallows node type Import"):
        run_python_bridge(
            "import math\nresult = 1",
            None,
            BridgeExecutionPolicy(timeout_seconds=1.0),
        )


def test_run_python_bridge_requires_result() -> None:
    with pytest.raises(PythonBridgeError, match="must assign 'result'"):
        run_python_bridge("value = 1", None, BridgeExecutionPolicy(timeout_seconds=1.0))
