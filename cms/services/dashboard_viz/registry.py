"""Visualization service registry for dashboard data.

Each dashboard has its own viz service module that reads a CSV file and
returns a dict of {figure_id: plotly_figure_json}. This module provides
the registry that dispatches to the correct service based on dashboard_slug.
"""

import importlib
from pathlib import Path
from typing import Any


def generate_figures(dashboard_slug: str, csv_file_path: str | Path) -> dict[str, Any]:
    """Generate all Plotly figures for a dashboard from its CSV file.

    Dispatches to the dashboard-specific viz service module. If no specific
    service exists for the given slug, returns an empty dict.

    Args:
        dashboard_slug: Identifies which viz service to use.
        csv_file_path: Path to the CSV file to read.

    Returns:
        Dict mapping figure_id to Plotly figure JSON.
    """
    registry: dict[str, str] = {
        # "serology-statistics": "cms.services.dashboard_viz.serology",
        # "vaccines": "cms.services.dashboard_viz.vaccines",
    }

    module_path = registry.get(dashboard_slug)
    if module_path is None:
        return {}

    module = importlib.import_module(module_path)
    return module.generate_figures(csv_file_path)
