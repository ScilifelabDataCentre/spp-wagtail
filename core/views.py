"""Shared utility views for the project.

Endpoints defined here are used across the system.
"""

from django.http import HttpRequest, JsonResponse


def healthz(_request: HttpRequest) -> JsonResponse:
    """Health check endpoint.

    Used for monitoring uptime of the service.
    Always returns a JSON object indicating that the service is running.

    Args:
        _request: Incoming HTTP request object (not used)

    Returns:
        JsonResponse: A JSON response indicating service status.
            Always returns 200 OK with {"status": "ok"} unless there is a server issue.

    """
    return JsonResponse({"status": "ok"})
