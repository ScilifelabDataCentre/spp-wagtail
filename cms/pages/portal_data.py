"""CMS page for accessing the Portal Data app."""
from __future__ import annotations

from django.db import models

from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

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

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("help_text"),
        FieldPanel("datatype"),
        FieldPanel("default_page_size"),
    ]

    subpage_types: list[str] = []

    class Meta:
        verbose_name = "Portal data page"

    def get_context(self, request, *args, **kwargs):  # noqa: ANN201
        context = super().get_context(request, *args, **kwargs)

        context.update(
            build_portal_data_context(
                request,
                datatype=self.datatype,
                default_size=self.default_page_size,
            )
        )

        return context