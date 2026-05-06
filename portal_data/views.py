"""Django views for browsing and exporting portal data mounted on the data PVC."""

from __future__ import annotations

import logging
import mimetypes
import os
import re
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from django.conf import settings
from django.core.cache import cache
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

logger = logging.getLogger("pages.portal_data.views")




# -------------------------------------------------------------------
# Views
# -------------------------------------------------------------------


class DataTypeList(View):
    """List available studies for a given data type with faceted search."""

    template_name = "portal_data/index.html"

    def get(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        """Build template context for the study list page."""
        datatype = str(kwargs["datatype"])
        ctx: dict[str, object] = {}

        if datatype not in SUPPORTED_TYPES:
            ctx["error"] = f"Unknown data type: {datatype}"
            return render(request, self.template_name, ctx)

        q = request.GET.get("q", "").strip()
        page = max(int(request.GET.get("page", "1")), 1)
        size = max(int(request.GET.get("size", "25")), 1)
        facet_names = request.GET.getlist("facet") or SUPPORTED_TYPES[datatype]["default_facets"]

        filter_fields = facet_names
        filters = {f: request.GET.getlist(f) for f in filter_fields if request.GET.getlist(f)}

        # Load from PVC
        all_items = _load_all_items(datatype)

        # Apply filters + search
        filtered_items = _apply_search_and_filters(all_items, q, filters)

        # Build facets from the current result set (so facets update when search/filters change)
        facets = _build_facets(
            items=filtered_items,
            facet_names=facet_names,
            filters=filters,
            datatype=datatype,  # from view / query_data_backend
            use_cache=(not q and not filters),
        )

        # Simple paging
        start = (page - 1) * size
        end = start + size
        page_items = filtered_items[start:end]

        has_facets = any(bool(buckets) for buckets in facets.values())
        ctx["has_facets"] = has_facets

        ctx.update(
            {
                "datatype": datatype,
                "datatype_label": SUPPORTED_TYPES[datatype]["label"],
                "query": q,
                "filters": filters,
                "facets": facets,
                "items": page_items,
                "total": len(filtered_items),
                "page": page,
                "size": size,
            }
        )
        return render(request, self.template_name, ctx)


class StudyFiles(View):
    """Render a simple file browser for a study directory on the PVC.

    Logs helpful debugging info if something goes wrong.
    """

    def get(
        self, request: HttpRequest, accession: str, *args: object, **kwargs: object
    ) -> HttpResponse:
        """Render a list of files available under the given study accession."""
        datatype = str(kwargs["datatype"])
        if datatype not in SUPPORTED_TYPES:
            raise Http404("Unknown data type")

        if not ACCESSION_RE.match(accession):
            raise Http404("Invalid accession")

        # Ensure DATA_ROOT exists on the cluster
        if not DATA_ROOT.is_dir():
            logger.error("DATA_ROOT does not exist or is not a directory: %s", DATA_ROOT)
            raise Http404("Study storage not available")

        study_dir = DATA_ROOT / accession
        if not study_dir.is_dir():
            logger.warning("Study directory not present: %s", study_dir)
            raise Http404("Study not found on this node")

        try:
            files = _list_study_files(study_dir)
        except Exception as err:
            logger.exception("Unexpected error listing files for %s/%s", datatype, accession)
            raise Http404("Could not list files") from err

        return render(
            request,
            "portal_data/study_files.html",
            {
                "datatype": datatype,
                "accession": accession,
                "files": files,
            },
        )


class DownloadStudyFile(View):
    """Stream a single file from the study directory.

    Protects against path traversal by resolving the requested path and ensuring it is
    inside the study directory. Logs errors to help diagnose cluster 500s.
    """

    def get(
        self,
        request: HttpRequest,
        accession: str,
        relpath: str,
        *args: object,
        **kwargs: object,
    ) -> HttpResponse:
        """Stream a single file from the given study.

        Validating that the path stays within the study directory.
        """
        datatype = str(kwargs["datatype"])
        if datatype not in SUPPORTED_TYPES:
            raise Http404("Unknown data type")

        if not ACCESSION_RE.match(accession):
            raise Http404("Invalid accession")

        # relpath may be URL-encoded in the URL; decode it once
        relpath = unquote(relpath)
        requested_path = Path(relpath)

        if requested_path.is_absolute():
            logger.warning("Rejecting absolute relpath request: %s", relpath)
            raise Http404("Invalid file path")

        # Ensure DATA_ROOT exists
        if not DATA_ROOT.is_dir():
            logger.error("DATA_ROOT not available: %s", DATA_ROOT)
            raise Http404("Study storage not available")

        study_dir = DATA_ROOT / accession
        if not study_dir.is_dir():
            logger.warning("Study directory missing for download: %s", study_dir)
            raise Http404("Study not found on this node")

        try:
            # Use resolve(strict=False) to avoid raising for strange mount points.
            # Then verify the resolved path remains inside the study directory.
            candidate = (study_dir / requested_path).resolve(strict=False)
            study_dir_resolved = study_dir.resolve(strict=False)
        except Exception as err:
            # If resolving fails for some reason, log and abort
            logger.exception("Path resolution failed for %s %s", study_dir, relpath)
            raise Http404("Invalid file path") from err

        # Ensure the requested file is under the study directory (path traversal protection).
        if not candidate.is_relative_to(study_dir_resolved):
            logger.warning(
                "Path traversal or invalid path detected. study_dir=%s candidate=%s",
                study_dir_resolved,
                candidate,
            )
            raise Http404("Invalid file path")

        if not candidate.exists() or not candidate.is_file():
            logger.warning("Requested file not found or not a file: %s", candidate)
            raise Http404("File not found")

        # Determine content type
        content_type, _ = mimetypes.guess_type(str(candidate))
        if content_type is None:
            content_type = "application/octet-stream"

        stack = ExitStack()
        try:
            f = stack.enter_context(candidate.open("rb"))
        except Exception as err:
            stack.close()
            logger.exception("Failed to open file for streaming: %s", candidate)
            # Return 404 rather than 500 to avoid leaking details to users, but log the exception.
            raise Http404("File not accessible") from err

        response = FileResponse(
            f,
            as_attachment=True,
            filename=candidate.name,
            content_type=content_type,
        )

        # Ensure file closed when response is closed
        original_close = response.close

        def cleanup_close(*cargs: object, **ckwargs: object) -> None:
            try:
                original_close(*cargs, **ckwargs)
            finally:
                stack.close()

        response.close = cleanup_close
        return response




