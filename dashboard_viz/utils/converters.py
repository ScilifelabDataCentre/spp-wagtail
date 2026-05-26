"""Plotly figure conversion utilities for PostgreSQL-safe JSON storage."""

import json
import math
from typing import Any

import plotly.graph_objects as go
import plotly.io as pio


def figure_to_json(fig: go.Figure) -> dict[str, Any]:
    """Convert a Plotly figure to a PostgreSQL-safe JSON dict.

    Replaces NaN/Infinity floats with None since JSONB rejects them.
    Leaves bdata arrays as-is (Plotly.js renders them natively).
    """

    def _sanitize(obj: object) -> object:
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize(item) for item in obj]
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        return obj

    raw = json.loads(pio.to_json(fig))
    return _sanitize(raw)
