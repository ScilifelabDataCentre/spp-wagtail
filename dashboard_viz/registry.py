"""Visualization service registry for dashboard data.

Each dashboard has its own viz service module that reads a CSV file and
returns a dict of {figure_id: plotly_figure_json}. This module provides
the registry that dispatches to the correct service based on dashboard_slug.
"""

import importlib
from pathlib import Path
from typing import Any, BinaryIO


def generate_figures(
    dashboard_slug: str,
    source_file: str | Path | BinaryIO,
) -> dict[str, Any]:
    """Generate all Plotly figures for a dashboard from its source data file.

    Dispatches to the dashboard-specific viz service module. If no specific
    service exists for the given slug, returns an empty dict.

    Args:
        dashboard_slug: Identifies which viz service to use.
        source_file: Path or file-like object for the source data file.

    Returns:
        Dict mapping figure_id to Plotly figure JSON.
    """
    registry: dict[str, str] = {
        "npc-statistics": "dashboard_viz.npc_statistics",
    }

    module_path = registry.get(dashboard_slug)
    if module_path is None:
        return {}

    module = importlib.import_module(module_path)
    return module.generate_figures(source_file)
