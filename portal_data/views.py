<<<<<<< HEAD
"""Django views for browsing and exporting portal data mounted on the data PVC."""
=======
"""View functions for the PortalDataPage."""
>>>>>>> 31d16f4 (Freya-2469: Moved view logic for portal data back into views.py (#50))

from __future__ import annotations

import logging
import mimetypes
from contextlib import ExitStack
from pathlib import Path
from urllib.parse import unquote

<<<<<<< HEAD
from django.conf import settings
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from portal_data.services import (
    ACCESSION_RE,
    get_data_root,
    get_datatype_config,
    list_study_files,
)

from .context import build_portal_data_context
=======
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from portal_data.services import ACCESSION_RE, get_data_root, get_datatype_config, list_study_files
>>>>>>> 31d16f4 (Freya-2469: Moved view logic for portal data back into views.py (#50))

from .context import build_portal_data_context

logger = logging.getLogger(__name__)


<<<<<<< HEAD
def _positive_int(value: str | None, default: int) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        return default
    return max(parsed, 1)


class DataTypeList(View):
    """Display the portal data index page for a specific data type."""

    template_name = "portal_data/index.html"

    def get(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        """Render the portal data index page for the requested data type."""
        datatype = str(kwargs["datatype"])
        context = build_portal_data_context(request, datatype=datatype)
        return render(request, self.template_name, context)

class StudyFiles(View):
    """Render a simple file browser for a study directory on the PVC.

    Logs helpful debugging info if something goes wrong.
    """

    def get(
        self, request: HttpRequest, accession: str, *args: object, **kwargs: object
    ) -> HttpResponse:
        """Render a list of files available under the given study accession."""
        datatype = str(kwargs["datatype"])
        if get_datatype_config(datatype) is None:
            raise Http404("Unknown data type")

        if not ACCESSION_RE.match(accession):
            raise Http404("Invalid accession")

        data_root = get_data_root()

        if not data_root.is_dir():
            logger.error("DATASETS_ROOT does not exist or is not a directory: %s", data_root)
            raise Http404("Study storage not available")

        portal_data_index_url = getattr(
            settings,
             "PORTAL_DATA_INDEX_URL",
             reverse("portal_data:index", kwargs={"datatype": datatype}),
        )

        study_dir = data_root / accession
        if not study_dir.is_dir():
            logger.warning("Study directory not present: %s", study_dir)
            raise Http404("Study not found on this node")

        try:
            files = list_study_files(study_dir)
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
                "portal_data_index_url": portal_data_index_url,
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
        if get_datatype_config(datatype) is None:
            raise Http404("Unknown data type")

        if not ACCESSION_RE.match(accession):
            raise Http404("Invalid accession")

        # relpath may be URL-encoded in the URL; decode it once
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




=======
def serve_study_files(
    request: HttpRequest, page: object, accession: str, template: str
) -> HttpResponse:
    """List files available for a given study accession."""
    if get_datatype_config(page.datatype) is None:
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
        logger.exception("Unexpected error listing files for %s/%s", page.datatype, accession)
        raise Http404("Could not list files") from err

    context = {
        "accession": accession,
        "files": files,
        "page": page,
        "portal_data_index_url": page.url,
    }
    return render(request, template, context)


def serve_download_file(
    request: HttpRequest, datatype: str, accession: str, relpath: str
) -> HttpResponse:
    """Stream a single file from a study directory.

    Protects against path traversal by resolving the requested path and
    confirming it stays inside the study directory.
    """

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
>>>>>>> 31d16f4 (Freya-2469: Moved view logic for portal data back into views.py (#50))
