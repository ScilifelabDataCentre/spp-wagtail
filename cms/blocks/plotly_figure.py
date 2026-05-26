"""Plotly figure block for rendering pre-computed charts."""

from wagtail.blocks import CharBlock, IntegerBlock, StructBlock, TextBlock, URLBlock


class PlotlyFigureBlock(StructBlock):
    """Renders a pre-computed Plotly chart from DashboardData.

    The figure_id field maps to a key in the DashboardData.data JSONField.
    The template reads the pre-computed Plotly JSON and renders it via
    Plotly.js on the client side.

    Attributes:
        figure_id: Key matching a figure in the DashboardData JSON dict.
        caption: Optional text displayed below the chart.
        height: Chart height in pixels.
        script_github_url: Link to the viz script in this repo on GitHub.
        alt_text: Accessibility description of the chart.
    """

    figure_id = CharBlock(
        required=True,
        help_text="Key matching a figure in the DashboardData JSON.",
    )
    caption = CharBlock(required=False, help_text="Text displayed below the chart.")
    height = IntegerBlock(default=500, help_text="Chart height in pixels.")
    script_github_url = URLBlock(
        required=False,
        help_text="Link to the viz script in this repo on GitHub.",
    )
    alt_text = TextBlock(
        required=True,
        help_text="Accessibility description of the chart.",
    )

    class Meta:
        """Block metadata."""

        template = "cms/blocks/plotly_figure.html"
        icon = "doc-full"
        label = "Plotly Figure"
