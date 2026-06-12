"""Serology Statistics visualisation code."""

from typing import Any

import plotly.express as px
import plotly.graph_objects as go
import polars as pl

from .utils.plotly import figure_to_json
from .utils.uploads import SourceFile, read_csv_dataframe

base_layout = {
    "autosize": True,
    "hovermode": "x unified",
    "legend_title": "<b>Test results</b>",
    "legend_traceorder": "reversed",
    "plot_bgcolor": "white",
}

base_xaxes = {
    "title": "<b>Date (year-week)</b>",
    "type": "category",
}

base_yaxes = {
    "gridcolor": "lightgrey",
    "linecolor": "black",
    "showgrid": True,
    "zeroline": True,
    "zerolinecolor": "black",
}

color_map = {"R&D": "#FCC892", "positive": "#F47BA4", "negative": "#1A6978"}


def _weekly_serology_fig(df: pl.DataFrame) -> go.Figure:
    """Generate Plotly figure for weekly serology test counts."""

    fig = px.bar(
        df,
        x="week",
        y="count",
        color="class",
        color_discrete_map=color_map,
        category_orders={"class": ["negative", "positive", "R&D"]},
    )
    fig.update_traces(hovertemplate=None)
    fig.update_layout(**base_layout, margin={"r": 0, "t": 0, "b": 0, "l": 0})
    fig.update_xaxes(**base_xaxes, linecolor="black")
    fig.update_yaxes(**base_yaxes, title="<b>Number of tests</b>")

    return fig


def _cumulative_serology_fig(df: pl.DataFrame) -> go.Figure:
    """Generate Plotly figure for cumulative serology test counts."""

    # Calculate cumulative sums within each class for the line plot
    df = df.with_columns(pl.col("count").cum_sum().over("class").alias("cumulative_sum"))

    # Calculate values for annotation
    sum_total = df["count"].sum()
    positive_count = df.filter(pl.col("class") == "positive")["count"].sum()
    sum_positive_negative = df.filter(pl.col("class").is_in(["positive", "negative"]))[
        "count"
    ].sum()
    proportion_positive = f"{100 * positive_count / sum_positive_negative:.2f}%"

    fig = px.line(
        df,
        x="week",
        y="cumulative_sum",
        color="class",
        color_discrete_map=color_map,
        markers=True,
    )
    fig.update_traces(hovertemplate=None, marker_color="white", marker_line_width=2, marker_size=8)

    fig.update_layout(**base_layout, margin={"r": 180, "t": 0, "b": 0, "l": 0})
    fig.update_xaxes(
        **base_xaxes,
        range=[0, df["class"].value_counts().max()],
    )
    fig.update_yaxes(
        **base_yaxes,
        title="<b>Cumulative number of tests</b>",
        range=[-1000, df["cumulative_sum"].max() + 10000],
    )

    fig.add_annotation(
        text=(
            f"<b>Sum total</b><br>{sum_total}<br><br>"
            f"<b>Proportion<br>positive</b><br>{proportion_positive}"
        ),
        showarrow=False,
        xref="paper",
        yref="paper",
        xanchor="left",
        x=1.02,
        y=0.585,
        bgcolor="#FFFFFF",
        bordercolor="black",
        borderwidth=2,
        borderpad=10,
        font_color="black",
        font_size=14,
    )

    return fig


def validate_source_columns(columns: list[str]) -> str | None:
    """Validate that the uploaded file has the expected columns for this dashboard."""
    expected_columns = {"week", "class", "count"}
    missing_columns = expected_columns - set(columns)
    if missing_columns:
        return f"Missing columns: {', '.join(missing_columns)}"
    return None


def generate_figures(source_file: SourceFile) -> dict[str, Any]:
    """Generate Plotly figures for the serology statistics dashboard."""

    figures = {}

    serology_df = read_csv_dataframe(source_file)

    figures["weekly_serology_plot"] = figure_to_json(_weekly_serology_fig(serology_df))

    figures["cumulative_serology_plot"] = figure_to_json(_cumulative_serology_fig(serology_df))

    return figures
