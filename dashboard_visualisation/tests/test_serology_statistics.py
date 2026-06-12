"""Tests for serology_statistics module."""

from unittest.mock import MagicMock, patch

import plotly.graph_objects as go
import polars as pl
from django.test import SimpleTestCase

from dashboard_visualisation.serology_statistics import (
    _cumulative_serology_fig,
    _weekly_serology_fig,
    generate_figures,
    validate_source_columns,
)


class TestsValidateSourceColumns(SimpleTestCase):
    """Tests for validate_source_columns function."""

    def test_valid_columns(self):
        """Test that valid columns pass validation."""
        self.assertIsNone(validate_source_columns(["week", "class", "count"]))

    def test_missing_column(self):
        """Test that missing columns are detected."""
        result = validate_source_columns(["week", "class"])

        self.assertEqual(result, "Missing columns: count")

    def test_multiple_missing_columns(self):
        """Test that multiple missing columns are detected."""
        result = validate_source_columns(["week"])

        self.assertIsNotNone(result)
        self.assertIn("class", result)
        self.assertIn("count", result)


class TestsWeeklySerologyFigure(SimpleTestCase):
    """Tests for _weekly_serology_fig function."""

    def setUp(self):
        """Set up test data."""
        self.df = pl.DataFrame(
            {
                "week": ["2024-01", "2024-01", "2024-02", "2024-02"],
                "class": ["negative", "positive", "negative", "positive"],
                "count": [10, 2, 15, 3],
            }
        )

    def test_returns_figure(self):
        """Test that a Plotly figure is returned."""
        fig = _weekly_serology_fig(self.df)

        self.assertIsInstance(fig, go.Figure)

    def test_contains_expected_classes(self):
        """Test that figure contains traces for expected classes."""
        fig = _weekly_serology_fig(self.df)
        trace_names = {trace.name for trace in fig.data}

        self.assertEqual(trace_names, {"negative", "positive"})

    def test_layout_configuration(self):
        """Test that figure layout is configured as expected."""
        fig = _weekly_serology_fig(self.df)

        self.assertEqual(fig.layout.hovermode, "x unified")
        self.assertEqual(fig.layout.plot_bgcolor, "white")
        self.assertEqual(fig.layout.xaxis.title.text, "<b>Date (year-week)</b>")
        self.assertEqual(fig.layout.yaxis.title.text, "<b>Number of tests</b>")

    def test_expected_colors(self):
        """Test that figure uses expected colors for classes."""
        fig = _weekly_serology_fig(self.df)
        colors = {trace.name: trace.marker.color for trace in fig.data}

        self.assertEqual(colors["negative"], "#1A6978")
        self.assertEqual(colors["positive"], "#F47BA4")


class TestsCumulativeSerologyFigure(SimpleTestCase):
    """Tests for _cumulative_serology_fig function."""

    def test_returns_figure(self):
        """Test that a Plotly figure is returned."""
        df = pl.DataFrame({"week": ["1"], "class": ["positive"], "count": [1]})

        fig = _cumulative_serology_fig(df)

        self.assertIsInstance(fig, go.Figure)

    def test_calculates_cumulative_sum(self):
        """Test that cumulative sums are calculated correctly."""
        df = pl.DataFrame({"week": ["1", "2"], "class": ["positive", "positive"], "count": [5, 7]})

        fig = _cumulative_serology_fig(df)

        trace = next(t for t in fig.data if t.name == "positive")

        self.assertEqual(list(trace.y), [5, 12])

    def test_annotation_contains_summary_values(self):
        """Test that annotation text contains summary values."""
        df = pl.DataFrame(
            {"week": ["1", "1"], "class": ["positive", "negative"], "count": [25, 75]}
        )

        fig = _cumulative_serology_fig(df)

        annotation = fig.layout.annotations[0]

        self.assertIn("100", annotation.text)
        self.assertIn("25.00%", annotation.text)

    def test_has_single_annotation(self):
        """Test that there is exactly one annotation."""
        df = pl.DataFrame(
            {"week": ["1", "1"], "class": ["positive", "negative"], "count": [25, 75]}
        )

        fig = _cumulative_serology_fig(df)

        self.assertEqual(len(fig.layout.annotations), 1)

    def test_marker_style(self):
        """Test that markers have expected style."""
        df = pl.DataFrame({"week": ["1"], "class": ["positive"], "count": [1]})

        fig = _cumulative_serology_fig(df)

        for trace in fig.data:
            self.assertEqual(trace.marker.size, 8)
            self.assertEqual(trace.marker.line.width, 2)


class TestsGenerateFigures(SimpleTestCase):
    """Tests for generate_figures function."""

    @patch("dashboard_visualisation.serology_statistics.figure_to_json")
    @patch("dashboard_visualisation.serology_statistics.read_csv_dataframe")
    def test_generate_figures(
        self, mock_read_csv_dataframe: MagicMock, mock_figure_to_json: MagicMock
    ):
        """Test that figures are generated and converted to JSON."""
        df = pl.DataFrame({"week": ["1"], "class": ["positive"], "count": [1]})

        mock_read_csv_dataframe.return_value = df
        mock_figure_to_json.side_effect = [{"weekly": "json"}, {"cumulative": "json"}]

        result = generate_figures(source_file="dummy")

        self.assertEqual(
            result,
            {
                "weekly_serology_plot": {"weekly": "json"},
                "cumulative_serology_plot": {"cumulative": "json"},
            },
        )
        mock_read_csv_dataframe.assert_called_once()
        self.assertEqual(mock_figure_to_json.call_count, 2)
