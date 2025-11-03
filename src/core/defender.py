"""Phase 3: Anomaly detection & attribution.

Implements AIR calculation and a simple poisoning detector that separates
control flow (invoked tool name) from data flow (invoked params).
"""

from __future__ import annotations

from typing import Any, Dict

from .ddg_builder import DDG


def compute_air(ddg: DDG, source_vertex: str, target_vertex: str) -> float:
    """Compute Anomaly Influence Ratio for a pair of vertices."""
    w_source = ddg.get_weight(source_vertex, target_vertex)
    w_user = ddg.get_weight("user_query", target_vertex)
    w_invoked = ddg.get_weight("invoked_tool", target_vertex)
    denom = w_user + w_invoked + 1e-10
    return float(w_source / denom)


def detect_poisoning(ddg: DDG, threshold: float = 0.5) -> Dict[str, Any]:
    """Detect poisoning and attribute the most likely source tool.

    Returns a dict with keys:
        poisoned: bool
        source: str | None
        air_control: float
        air_data: float
    """
    best: Dict[str, Any] = {"poisoned": False, "source": None, "air_control": 0.0, "air_data": 0.0}

    for tool in ddg.uninvoked_tools:
        air_control = compute_air(ddg, tool, "invoked_tool_name")
        air_data = compute_air(ddg, tool, "invoked_params")
        score = max(air_control, air_data)
        if score > best["air_control"]:
            best = {
                "poisoned": score > threshold,
                "source": tool if score > threshold else None,
                "air_control": air_control,
                "air_data": air_data,
            }

    return best


__all__ = ["compute_air", "detect_poisoning"]
