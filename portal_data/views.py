"""View helpers for the PortalDataPage routable subroutes."""

from __future__ import annotations

import logging
import mimetypes
from contextlib import ExitStack
from pathlib import Path
from urllib.parse import unquote

from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from portal_data.services import (
    ACCESSION_RE,
    get_data_root,
    get_datatype_config,
    list_study_files,
)

logger = logging.getLogger(__name__)


def serve_study_files(
    request: HttpRequest,
    page: object,
    accession: str,
    template: str,
) -> HttpResponse:
    """List files available for a given study accession."""
    datatype = str(getattr(page, "datatype", "")).strip()

    if get_datatype_config(datatype) is None:
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
        logger.exception("Unexpected error listing files for %s/%s", datatype, accession)
        raise Http404("Could not list files") from err

    context = {
        "accession": accession,
        "files": files,
        "page": page,
        "portal_data_index_url": getattr(page, "url", ""),
    }
    return render(request, template, context)


def serve_download_file(
    request: HttpRequest,
    datatype: str,
    accession: str,
    relpath: str,
) -> HttpResponse:
    """Stream a single local file from the study directory.

    This is the filesystem/PVC implementation. The StorageGRID implementation
    should later branch here and redirect to a pre-signed S3 URL instead of
    streaming bytes through Django.
    """
    datatype = str(datatype).strip()

    if get_datatype_config(datatype) is None:
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
        file_obj = stack.enter_context(candidate.open("rb"))
    except Exception as err:
        stack.close()
        logger.exception("Failed to open file for streaming: %s", candidate)
        raise Http404("File not accessible") from err

    response = FileResponse(
        file_obj,
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
