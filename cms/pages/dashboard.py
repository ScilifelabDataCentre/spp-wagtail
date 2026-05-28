"""CMS page for individual dashboards."""

from typing import Any

from django.db import models
from django.http import HttpRequest
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.fields import StreamField
from wagtail.images import get_image_model_string
from wagtail.models import Page

from cms.blocks import AlertBlock, LastUpdatedBlock, PlotlyFigureBlock, StaticFigureBlock

DATA_STATUS_CHOICES = [
    ("active", "Active"),
    ("historic", "Historic"),
]


class DashboardPage(Page):
    """A page representing a single data dashboard.

    Displays data visualisations (Plotly charts or static figures) along with
    explanatory text. Card fields (description, image, data_status) are used
    by the parent DashboardIndexPage for the card grid listing.

    Attributes:
        description: Brief text for the index card.
        image: Thumbnail image for the index card.
        data_status: Whether the dashboard data is active or historic.
        content: StreamField with text, alerts, and figure blocks.
    """

    template = "cms/pages/dashboard.html"
    parent_page_types = ["cms.DashboardIndexPage"]
    subpage_types = []

    description = models.CharField(max_length=255, blank=False)
    image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=False,
        on_delete=models.PROTECT,
        related_name="+",
    )
    data_status = models.CharField(
        max_length=50,
        choices=DATA_STATUS_CHOICES,
    )
    content = StreamField(
        [
            ("text", RichTextBlock()),
            ("alert", AlertBlock()),
            ("last_updated", LastUpdatedBlock()),
            ("plotly_figure", PlotlyFigureBlock()),
            ("static_figure", StaticFigureBlock()),
        ],
        blank=False,
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel(
                    "description",
                    help_text="Brief text displayed on the dashboard index card.",
                ),
                FieldPanel(
                    "image",
                    help_text="Thumbnail image displayed on the dashboard index card.",
                ),
            ],
            heading="Card details",
        ),
        FieldPanel(
            "data_status",
            help_text="Whether this dashboard's data is active or historic.",
        ),
        FieldPanel(
            "content",
            help_text="Main content: text, charts, and figures.",
        ),
    ]

    def get_context(self, request: HttpRequest) -> dict[str, Any]:
        """Add DashboardData figures, CSV URL, and parent heading to template context."""

        # Importing here to avoid circular import issues
        from cms.pages.dashboard_index import DashboardIndexPage
        from cms.snippets.dashboard_data import DashboardData

        context = super().get_context(request)
        dashboard_data = DashboardData.get_data(self.slug)
        context["dashboard_data"] = dashboard_data
        context["figures"] = dashboard_data.data if dashboard_data else {}
        context["data_updated_at"] = dashboard_data.data_updated_at if dashboard_data else None
        context["source_file_hash"] = dashboard_data.source_file_hash if dashboard_data else ""

        parent = self.get_ancestors().type(DashboardIndexPage).specific().first()
        context["page_heading"] = parent.title if parent else ""
        return context
