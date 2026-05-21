"""Service functions for the Catalogue page."""

from typing import Any

from django.http import Http404
from django.http.request import QueryDict
from django.utils.text import slugify

SEARCH_MAX_LENGTH = 100


def validate_filters(
    querydict: QueryDict,
    valid_types: list[str] | None = None,
    search_max_length: int = SEARCH_MAX_LENGTH,
) -> dict[str, Any]:
    """Validate catalogue filter query parameters.

    Ensures that:
        - only allowed query parameters are present
        - search input length is reasonable
        - list-based filters are bounded in size
        - individual values are not excessively large

    Args:
        querydict: Incoming request query parameters (typically ``request.GET``).
        valid_types: A list of allowed catalogue type values.
        search_max_length: Maximum allowed length for the search query.

    Returns:
        A normalized dictionary containing validated filter values.

    Raises:
        Http404: If invalid or unexpected query parameters are detected.

    Example:
        .. code-block:: python

            filters = validate_filters(request.GET)
    """

    validated_filters = {"search": "", "type": []}

    if not querydict:
        return validated_filters

    # Reject unexpected parameters
    for key in querydict:
        if key not in validated_filters:
            raise Http404(f"Invalid query parameter: {key}")

    # Validate search
    search = querydict.get("search", "").strip().lower()
    if len(search) > search_max_length:
        raise Http404("Search query too long")
    validated_filters["search"] = search

    # Validate catalogue types
    types = querydict.getlist("type")
    if valid_types and any(cat_type not in map(slugify, valid_types) for cat_type in types):
        raise Http404("Invalid catalogue type value")
    if valid_types and len(types) > len(valid_types):
        raise Http404("Too many catalogue types selected")
    validated_filters["type"] = types

    return validated_filters
