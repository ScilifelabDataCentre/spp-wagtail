"""CMS page for accessing the Portal Data app."""

from __future__ import annotations

import logging
import mimetypes
from contextlib import ExitStack
from pathlib import Path
from urllib.parse import unquote

from django.db import models
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.contrib.routable_page.models import RoutablePageMixin, path
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page

from cms.blocks import AlertBlock
from portal_data.context import build_portal_data_context
from portal_data.services import ACCESSION_RE, get_data_root, get_datatype_config, list_study_files

logger = logging.getLogger(__name__)


class PortalDataPage(RoutablePageMixin, Page):
    """CMS-managed wrapper around the portal_data dataset browser.

    RoutablePageMixin lets sub-paths (file browser, file download) be handled
    directly by this page, removing the need for portal_data.urls,
    portal_data.wagtail_urls, and their corresponding root urlconf includes.
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
        FieldPanel("datatype",
                   help_text=(
                       "Type of datapage to be created, right now only Metabolomics is available"
                   )),
        FieldPanel("default_page_size",
                   help_text=(
                       "Number of items to display per page, default=25"
                   )),
        FieldPanel("content",
                   help_text=(
                       "Additional content for the Portal data page. Will be displayed "
                   )),
    ]

    class Meta:
        """Metadata options for the portal data page."""

        verbose_name = "Portal data page"

    def get_context(self, request):  # noqa: ANN201, ANN002, ANN003, ANN001
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

    # ------------------------------------------------------------------ #
    # Routes                                                             #
    # ------------------------------------------------------------------ #

    @path("")
    def index(self, request: HttpRequest) -> HttpResponse:
        """Render the dataset listing — the page's main view."""
        context = self.get_context(request)

        if getattr(request, "htmx", False):
            return render(request, "portal_data/partials/listing.html", context)

        return render(request, "portal_data/index.html", context)

    @path("<slug:accession>/files/")
    def study_files(self, request: HttpRequest, accession: str) -> HttpResponse:
        """List files available for a given study accession."""
        if get_datatype_config(self.datatype) is None:
            raise Http404("Unknown data type")

        if not ACCESSION_RE.match(accession):
            raise Http404("Invalid accession")

        data_root = get_data_root()
        if not data_root.is_dir():
            logger.error("DATASETS_ROOT does not exist or is not a directory: %s", data_root)
            raise Http404("Study storage not available")

        study_dir = data_root / accession
        if not study_dir.is_dir():
            logger.warning("Study directory not present: %s", study_dir)
            raise Http404("Study not found on this node")

        try:
            files = list_study_files(study_dir)
        except Exception as err:
            logger.exception("Unexpected error listing files for %s/%s", self.datatype, accession)
            raise Http404("Could not list files") from err

        context = self.get_context(request)
        context.update(
            {
                "accession": accession,
                "files": files,
                # self.url is the canonical Wagtail URL for this page instance.
                "portal_data_index_url": self.url,
            }
        )
        return render(request, "portal_data/study_files.html", context)

    @path("<slug:accession>/files/<path:relpath>/")
    def download_file(self, request: HttpRequest, accession: str, relpath: str) -> HttpResponse:
        """Stream a single file from a study directory.

        Protects against path traversal by resolving the requested path and
        confirming it stays inside the study directory.
        """
        if get_datatype_config(self.datatype) is None:
            raise Http404("Unknown data type")

        if not ACCESSION_RE.match(accession):
            raise Http404("Invalid accession")

        relpath = unquote(relpath)
        requested_path = Path(relpath)

        if requested_path.is_absolute():
            logger.warning("Rejecting absolute relpath request: %s", relpath)
            raise Http404("Invalid file path")

        data_root = get_data_root()
        if not data_root.is_dir():
            logger.error("DATASETS_ROOT does not exist or is not a directory: %s", data_root)
            raise Http404("Study storage not available")

        study_dir = data_root / accession
        if not study_dir.is_dir():
            logger.warning("Study directory missing for download: %s", study_dir)
            raise Http404("Study not found on this node")

        try:
            candidate = (study_dir / requested_path).resolve(strict=False)
            study_dir_resolved = study_dir.resolve(strict=False)
        except Exception as err:
            logger.exception("Path resolution failed for %s %s", study_dir, relpath)
            raise Http404("Invalid file path") from err

        if not candidate.is_relative_to(study_dir_resolved):
            logger.warning(
                "Path traversal detected. study_dir=%s candidate=%s",
                study_dir_resolved,
                candidate,
            )
            raise Http404("Invalid file path")

        if not candidate.exists() or not candidate.is_file():
            logger.warning("Requested file not found or not a file: %s", candidate)
            raise Http404("File not found")

        content_type, _ = mimetypes.guess_type(str(candidate))
        if content_type is None:
            content_type = "application/octet-stream"

        stack = ExitStack()
        try:
            f = stack.enter_context(candidate.open("rb"))
        except Exception as err:
            stack.close()
            logger.exception("Failed to open file for streaming: %s", candidate)
            raise Http404("File not accessible") from err

        response = FileResponse(
            f,
            as_attachment=True,
            filename=candidate.name,
            content_type=content_type,
        )

        original_close = response.close

        def cleanup_close(*args: object, **kwargs: object) -> None:
            try:
                original_close(*args, **kwargs)
            finally:
                stack.close()

        response.close = cleanup_close
        return response
