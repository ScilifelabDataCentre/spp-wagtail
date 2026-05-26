"""Visualization service for the NPC SARS-CoV-2 test statistics dashboard.

Generates 6 Plotly figures from the NPC statistics CSV. The CSV has columns:
    - date: Test date
    - class: Test result category (positive, negative, invalid/inconclusive)
    - count: Number of tests

This is a direct port of the legacy scripts in
old-portal/pathogens-portal-visualisations/npctests/.
"""

from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px

from dashboard_viz.utils import figure_to_json


def _total_tests(npc_data: pd.DataFrame) -> dict[str, Any]:
    """Horizontal bar chart of total tests by class.

    Port of npc_total_tests.py.
    """
    total_tests = npc_data["count"].sum()
    total_positive = npc_data[npc_data["class"] == "positive"]["count"].sum()
    total_negative = npc_data[npc_data["class"] == "negative"]["count"].sum()
    total_inv = npc_data[npc_data["class"] == "invalid/inconclusive"]["count"].sum()

    data = {
        "class": ["Positive", "Negative", "Invalid/Inconclusive"],
        "Count": [total_positive, total_negative, total_inv],
    }
    df = pd.DataFrame(data)

    fig = px.bar(df, y="class", x="Count", text="Count", orientation="h")
    fig.update_traces(
        textposition="outside",
        marker_color=["#F47BA4", "#1A6978", "#FCC892"],
        marker_line_color="black",
        marker_line_width=2,
        hovertemplate="Class: <b>%{y}</b><br>Count: <b>%{x}</b>",
        hoverlabel_bgcolor="white",
    )
    fig.update_layout(
        title_text="<b>Total number of tests</b>",
        plot_bgcolor="white",
        autosize=True,
        title_x=0.5,
        xaxis_title=None,
        yaxis_title=None,
        margin={"l": 0, "r": 200, "t": 50, "b": 0},
    )
    fig.update_xaxes(
        range=[0, 600000],
        showgrid=True,
        linecolor="black",
        gridcolor="lightgrey",
        zeroline=True,
        zerolinecolor="black",
    )
    fig.update_yaxes(linecolor="black", zeroline=True, zerolinecolor="black")
    fig.add_annotation(
        x=1.02,
        y=0.8,
        xanchor="left",
        xref="paper",
        yref="paper",
        text=f"<b>Sum total</b><br>{total_tests}",
        showarrow=False,
        font_size=14,
        align="center",
        bordercolor="black",
        borderwidth=2,
        borderpad=10,
        bgcolor="white",
    )
    return figure_to_json(fig)


def _tests_daily(npc_data: pd.DataFrame) -> dict[str, Any]:
    """Stacked bar chart of daily tests by class.

    Port of npc_tests_daily.py.
    """
    fig = px.bar(
        npc_data,
        x="date",
        y="count",
        color="class",
        labels={"count": "Number of Tests", "date": "Date", "class": "<b>Test Results</b>"},
        color_discrete_map={
            "invalid/inconclusive": "#FCC892",
            "positive": "#F47BA4",
            "negative": "#1A6978",
        },
        category_orders={"class": ["positive", "negative", "invalid/inconclusive"]},
    )
    fig.update_traces(hovertemplate=None)
    fig.update_layout(
        title_text=None,
        plot_bgcolor="white",
        autosize=True,
        xaxis_title="<b>Date</b>",
        yaxis_title="<b>Number of tests</b>",
        margin={"r": 0, "t": 0, "b": 0, "l": 0},
        hovermode="x unified",
        legend_traceorder="reversed",
    )
    fig.update_xaxes(linecolor="black", zeroline=True, zerolinecolor="black")
    fig.update_yaxes(linecolor="black", zeroline=True, gridcolor="lightgrey", zerolinecolor="black")
    return figure_to_json(fig)


def _tests_weekly(npc_data: pd.DataFrame) -> dict[str, Any]:
    """Stacked bar chart of weekly tests by class.

    Port of npc_tests_weekly.py.
    """
    weekly_data = npc_data.copy()
    weekly_data["date"] = pd.to_datetime(weekly_data["date"])
    weekly_data["week_of_year"] = weekly_data["date"].dt.isocalendar().week.astype(int)

    grouped_data = weekly_data.groupby(["week_of_year", "class"])["count"].sum().reset_index()

    fig = px.bar(
        grouped_data,
        x="week_of_year",
        y="count",
        color="class",
        labels={"count": "Number of Tests", "date": "Date", "class": "<b>Test Results</b>"},
        color_discrete_map={
            "invalid/inconclusive": "#FCC892",
            "positive": "#F47BA4",
            "negative": "#1A6978",
        },
        category_orders={"class": ["positive", "negative", "invalid/inconclusive"]},
    )
    fig.update_traces(hovertemplate=None)
    fig.update_layout(
        title_text=None,
        plot_bgcolor="white",
        autosize=True,
        xaxis_title="<b>Week</b>",
        yaxis_title="<b>Number of tests</b>",
        margin={"r": 0, "t": 0, "b": 0, "l": 0},
        hovermode="x unified",
        legend_traceorder="reversed",
    )
    fig.update_xaxes(linecolor="black", zeroline=True, zerolinecolor="black")
    fig.update_yaxes(linecolor="black", gridcolor="lightgrey", zeroline=True, zerolinecolor="black")
    return figure_to_json(fig)


def _positive_fraction_daily(npc_data: pd.DataFrame) -> dict[str, Any]:
    """Bar chart of daily positive test fraction.

    Port of npc_positiveTests_fraction_daily.py.
    """
    only_positive_data = npc_data[npc_data["class"] == "positive"].copy()
    filtered_data = npc_data[npc_data["class"] != "invalid/inconclusive"].copy()
    only_positive_data["total_tests"] = filtered_data.groupby("date")["count"].transform("sum")
    only_positive_data["fraction"] = (
        only_positive_data["count"] / only_positive_data["total_tests"] * 100
    )

    fig = px.bar(only_positive_data, x="date", y="fraction")
    fig.update_traces(hovertemplate=None, hoverlabel_bgcolor="white", marker_color="#F47BA4")
    fig.update_layout(
        title_text=None,
        plot_bgcolor="white",
        autosize=True,
        xaxis_title="<b>Date</b>",
        yaxis_title="<b>Fraction Positive</b>",
        hovermode="x unified",
    )
    fig.update_xaxes(linecolor="black", zeroline=True, zerolinecolor="black")
    fig.update_yaxes(
        linecolor="black",
        zeroline=True,
        zerolinecolor="black",
        ticksuffix="%",
        gridcolor="lightgrey",
    )
    return figure_to_json(fig)


def _positive_fraction_weekly(npc_data: pd.DataFrame) -> dict[str, Any]:
    """Bar chart of weekly positive test fraction.

    Port of npc_positiveTests_fraction_weekly.py.
    """
    data = npc_data.copy()
    data["date"] = pd.to_datetime(data["date"])
    data["week_of_year"] = data["date"].dt.isocalendar().week.astype(int)

    only_positive_data = data[data["class"] == "positive"].copy()
    filtered_data = data[data["class"] != "invalid/inconclusive"].copy()
    only_positive_data["total_tests"] = filtered_data.groupby("date")["count"].transform("sum")
    only_positive_data["fraction"] = (
        only_positive_data["count"] / only_positive_data["total_tests"] * 100
    )

    grouped_data = (
        only_positive_data.groupby(["week_of_year"])
        .agg({"count": "sum", "total_tests": "sum"})
        .reset_index()
    )
    grouped_data["fraction"] = grouped_data["count"] / grouped_data["total_tests"]

    fig = px.bar(grouped_data, x="week_of_year", y="fraction")
    fig.update_traces(hovertemplate=None, hoverlabel_bgcolor="white", marker_color="#F47BA4")
    fig.update_layout(
        title_text=None,
        plot_bgcolor="white",
        autosize=True,
        xaxis_title="<b>Week</b>",
        yaxis_title="<b>Fraction Positive</b>",
        hovermode="x unified",
    )
    fig.update_xaxes(linecolor="black", zeroline=True, zerolinecolor="black")
    fig.update_yaxes(
        linecolor="black",
        zeroline=True,
        zerolinecolor="black",
        tickformat="0%",
        gridcolor="lightgrey",
    )
    return figure_to_json(fig)


def _cumulative_tests(npc_data: pd.DataFrame) -> dict[str, Any]:
    """Line chart of cumulative tests by class.

    Port of npc_cumulative_tests.py.
    """
    cum_data = npc_data.copy()
    cum_data["date"] = pd.to_datetime(cum_data["date"])
    cum_data = cum_data.sort_values(by="date")
    cum_data["cumulative sum"] = cum_data.groupby("class")["count"].cumsum()
    cum_data["date"] = cum_data["date"].dt.strftime("%Y-%m-%d")

    fig = px.line(
        cum_data,
        x="date",
        y="cumulative sum",
        color="class",
        labels={"class": "<b>Test Results</b>"},
        color_discrete_map={
            "invalid/inconclusive": "#FCC892",
            "positive": "#F47BA4",
            "negative": "#1A6978",
        },
        category_orders={"class": ["positive", "negative", "invalid/inconclusive"]},
        markers=True,
    )
    fig.update_traces(
        hovertemplate=None,
        marker_color="white",
        marker_line_width=2,
        marker_size=8,
    )
    fig.update_layout(
        plot_bgcolor="white",
        autosize=True,
        hovermode="x unified",
        legend_traceorder="reversed",
    )
    fig.update_xaxes(
        type="category",
        title="<b>Date</b>",
        nticks=10,
        zeroline=True,
        tickangle=45,
        zerolinecolor="black",
    )
    fig.update_yaxes(
        title="<b>Cumulative number of tests</b>",
        linecolor="black",
        showgrid=True,
        gridcolor="lightgrey",
        zeroline=True,
        zerolinecolor="black",
    )
    return figure_to_json(fig)


def generate_figures(csv_file_path: str | Path) -> dict[str, Any]:
    """Generate all 6 NPC statistics Plotly figures from the CSV.

    Args:
        csv_file_path: Path to the NPC statistics CSV file.

    Returns:
        Dict mapping figure_id to Plotly figure JSON.
    """
    npc_data = pd.read_csv(csv_file_path)

    return {
        "npc_total_tests": _total_tests(npc_data),
        "npc_tests_daily": _tests_daily(npc_data),
        "npc_tests_weekly": _tests_weekly(npc_data),
        "npc_positive_fraction_daily": _positive_fraction_daily(npc_data),
        "npc_positive_fraction_weekly": _positive_fraction_weekly(npc_data),
        "npc_cumulative_tests": _cumulative_tests(npc_data),
    }
