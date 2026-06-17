"""CMS page for accessing the Portal Data app."""

from __future__ import annotations

import logging
from typing import Any

from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.contrib.routable_page.models import RoutablePageMixin, path
from wagtail.fields import StreamField
from wagtail.models import Page

from cms.blocks import AlertBlock
from portal_data.context import build_portal_data_context
from portal_data.views import serve_download_file, serve_study_files

logger = logging.getLogger(__name__)


class PortalDataPage(RoutablePageMixin, Page):
    """CMS-managed wrapper around the portal_data dataset browser.

    RoutablePageMixin lets sub-paths for file browsing and file downloads be
    handled directly by this page. The portal_data app keeps the backend/data
    access logic, while Wagtail owns the public page URL and editorial content.
    """

    subpage_types: list[str] = []

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
        FieldPanel(
            "datatype",
            help_text=(
                "Type of data page to create. "
                "Currently only Metabolomics is available."
            ),
        ),
        FieldPanel(
            "default_page_size",
            help_text="Number of items to display per page. Default is 25.",
        ),
        FieldPanel(
            "content",
            help_text="Main editable content for the Portal data page.",
        ),
    ]

    class Meta:
        """Metadata options for the portal data page."""

        verbose_name = "Portal data page"

    def get_context(self, request: HttpRequest) -> dict[str, Any]:
        """Build the template context for the portal data page."""
        context = super().get_context(request)

        context.update(
            build_portal_data_context(
                request,
                datatype=self.datatype.strip(),
                default_size=self.default_page_size,
            )
        )

        return context

    @path("")
    def index(self, request: HttpRequest) -> HttpResponse:
        """Render the dataset listing."""
        context = self.get_context(request)

        if getattr(request, "htmx", False):
            return render(
                request,
                "cms/pages/portal_data/partials/listing.html",
                context,
            )

        return render(request, "cms/pages/portal_data/index.html", context)

    @path("<slug:accession>/files/")
    def study_files(self, request: HttpRequest, accession: str) -> HttpResponse:
        """List files available for a given study accession."""
        return serve_study_files(
            request=request,
            page=self,
            accession=accession,
            template="cms/pages/portal_data/study_files.html",
        )

    @path("<slug:accession>/files/<path:relpath>/")
    def download_file(
        self,
        request: HttpRequest,
        accession: str,
        relpath: str,
    ) -> HttpResponse:
        """Serve or redirect to a single file for a study."""
        return serve_download_file(
            request=request,
            datatype=self.datatype,
            accession=accession,
            relpath=relpath,
        )
