"""Minimal viz module for ``dashboard_visualisation`` registry tests only."""

from typing import Any

import plotly.express as px

from dashboard_visualisation.utils import figure_to_json
from dashboard_visualisation.utils.uploads import SourceFile, read_csv_dataframe, rewind_source_file

REQUIRED_SOURCE_COLUMNS = frozenset({"date", "value"})


def validate_source_columns(columns: list[str]) -> str | None:
    """Return an error message when required CSV columns are missing."""
    found = {column.strip() for column in columns}
    if not REQUIRED_SOURCE_COLUMNS.issubset(found):
        return f"CSV must include columns: date, value (found: {', '.join(columns)})."
    return None


def generate_figures(source_file: SourceFile) -> dict[str, Any]:
    """Build a single sample figure so registry dispatch can be tested."""
    rewind_source_file(source_file)
    data = read_csv_dataframe(source_file)
    fig = px.bar(data, x="date", y="value")
    return {"sample_chart": figure_to_json(fig)}
