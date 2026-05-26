"""CMS page for dashboard index."""

from typing import Any

from django.http import HttpRequest
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.fields import StreamField
from wagtail.models import Page

from cms.blocks import AlertBlock


class DashboardIndexPage(Page):
    """A page listing all dashboards.

    This page is the parent of all DashboardPage instances. Only one instance
    can exist. Child dashboard pages are listed as cards grouped by data_status.

    Attributes:
        content: Optional introductory content above the dashboard listing.
    """

    max_count = 1
    template = "cms/pages/dashboard_index.html"
    parent_page_types = ["cms.HomePage"]
    subpage_types = ["cms.DashboardPage"]

    content = StreamField(
        [
            ("text", RichTextBlock()),
            ("alert", AlertBlock()),
        ],
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("content"),
    ]

    def get_context(self, request: HttpRequest) -> dict[str, Any]:
        """Add child dashboards grouped by data_status to the context."""

        # Importing here to avoid circular imports
        from cms.pages.dashboard import DATA_STATUS_CHOICES, DashboardPage

        context = super().get_context(request)
        context["dashboards"] = {}
        for status_key, _label in DATA_STATUS_CHOICES:
            dashboards = (
                self.get_children()
                .type(DashboardPage)
                .live()
                .public()
                .filter(dashboardpage__data_status=status_key)
                .specific()
                .order_by("title")
            )
            if dashboards:
                context["dashboards"][status_key] = dashboards
        return context
