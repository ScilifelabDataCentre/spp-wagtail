"""Last updated block for dashboard data freshness dates."""

from wagtail.blocks import CharBlock, StructBlock


class LastUpdatedBlock(StructBlock):
    """Renders the dashboard data freshness date from DashboardData.

    The date comes from ``DashboardData.data_updated_at`` (set in the upload
    snippet), passed through ``DashboardPage.get_context()`` as ``data_updated_at``.
    Wagtail merges page context into block templates automatically, so this block
    does not need a custom ``get_context``. If no date is set, nothing is rendered.

    Attributes:
        label: Heading before the date (default "Last updated").
        suffix: Optional text after the date (e.g. "(no longer updating)").
    """

    label = CharBlock(
        required=False,
        default="Last updated",
        help_text='Label shown before the date (e.g. "All data last updated").',
    )
    suffix = CharBlock(
        required=False,
        help_text='Optional text after the date (e.g. "(no longer updating)").',
    )

    class Meta:
        """Block metadata."""

        template = "cms/blocks/last_updated.html"
        icon = "time"
        label = "Last updated"
        help_text = (
            "Shows the data freshness date from Dashboard Data Upload "
            "(data_updated_at). Renders nothing if the date is not set."
        )
