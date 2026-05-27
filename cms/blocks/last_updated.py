"""Last updated block for dashboard data freshness dates."""

from typing import Any

from wagtail.blocks import CharBlock, StructBlock


class LastUpdatedBlock(StructBlock):
    """Renders the dashboard data freshness date from DashboardData.

    The date comes from ``DashboardData.data_updated_at`` (set in the upload
    snippet), passed through ``DashboardPage.get_context()`` as ``data_updated_at``.
    If no date is set, nothing is rendered.

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

    def get_context(
        self,
        value: dict[str, Any],
        parent_context: dict | None = None,
    ) -> dict[str, Any]:
        """Expose the public data freshness date from the page context."""
        context = super().get_context(value, parent_context)
        parent_context = parent_context or {}
        context["data_updated_at"] = parent_context.get("data_updated_at")
        return context

    class Meta:
        """Block metadata."""

        template = "cms/blocks/last_updated.html"
        icon = "time"
        label = "Last updated"
        help_text = (
            "Shows the data freshness date from Dashboard Data Upload "
            "(data_updated_at). Renders nothing if the date is not set."
        )
