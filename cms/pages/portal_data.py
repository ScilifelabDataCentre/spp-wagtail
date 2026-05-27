"""CMS page for accessing the Portal Data app."""
from __future__ import annotations

from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page

from cms.blocks import AlertBlock
from portal_data.context import build_portal_data_context


class PortalDataPage(Page):
    """CMS-managed wrapper around the portal_data dataset browser."""

    template = "portal_data/index.html"

    intro = RichTextField(blank=True)
    help_text = RichTextField(blank=True)

    datatype = models.CharField(
        max_length=64,
        choices=[
            ("metabolomics", "Metabolomics"),
        ],
        default="metabolomics",
    )

    default_page_size = models.PositiveIntegerField(default=25)

    content = StreamField(
        [
            ("text", RichTextBlock()),
            ("alert", AlertBlock()),
        ],
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("datatype"),
        FieldPanel("default_page_size"),
        FieldPanel("content"),
    ]

    subpage_types: list[str] = []

    class Meta:
        """Metadata options for the portal data page."""

        verbose_name = "Portal data page"

    def get_context(self, request, *args, **kwargs):  # noqa: ANN201, ANN002, ANN003, ANN001
        """Build the template context for the portal data page."""
        context = super().get_context(request, *args, **kwargs)

        context.update(
            build_portal_data_context(
                request,
                datatype=self.datatype.strip(),
                default_size=self.default_page_size,
            )
        )

        return context
