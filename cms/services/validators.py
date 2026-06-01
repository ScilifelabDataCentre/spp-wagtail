"""Validator utilities that can be used across the CMS."""

from typing import Any

from django.http import Http404
from django.http.request import QueryDict
from django.utils.text import slugify

SEARCH_MAX_LENGTH = 100


def validate_filters(
    querydict: QueryDict,
    valid_topics: list[str] | None = None,
    valid_types: list[str] | None = None,
    expected_keys: set[str] | None = None,
    search_max_length: int = SEARCH_MAX_LENGTH,
) -> dict[str, Any]:
    """Validate request filter query parameters.

    Ensures that:
        - only allowed query parameters are present
        - search input length is reasonable
        - list-based filters are bounded in size
        - individual values are not excessively large

    Args:
        querydict: Incoming request query parameters (typically ``request.GET``).
        valid_topics: Optional list of allowed topic values.
        valid_types: Optional list of allowed article type values.
        expected_keys: Optional set of allowed query parameter keys
            (default: {"search", "topic", "type"}).
        search_max_length: Optional maximum allowed length for the search query.

    Returns:
        A normalized dictionary containing validated filter values.

    Raises:
        Http404: If invalid or unexpected query parameters are detected.

    Example:
        .. code-block:: python

            filters = validate_filters(request.GET)
    """
    allowed_keys = {"search", "topic", "type"}

    expected_keys = expected_keys or allowed_keys
    invalid_expected_keys = expected_keys - allowed_keys
    if invalid_expected_keys:
        raise ValueError(
            f"Unsupported expected_keys: {invalid_expected_keys}. Allowed keys are: {allowed_keys}"
        )

    validated_filters = {}

    if not querydict:
        return validated_filters

    # Reject unexpected parameters
    for key in querydict:
        if key not in expected_keys:
            raise Http404(f"Invalid query parameter: {key}")
        else:
            if key == "search":
                value = querydict.get(key, "").strip().lower()
                if len(value) > search_max_length:
                    raise Http404("Search query too long")
            else:
                value = querydict.getlist(key)
                valid_choices = valid_topics if key == "topic" else valid_types
                if valid_choices and len(value) > len(valid_choices):
                    raise Http404(f"Too many {key} values selected")
                if valid_choices and any(v not in map(slugify, valid_choices) for v in value):
                    raise Http404(f"Invalid {key} value")
            validated_filters[key] = value

    return validated_filters
