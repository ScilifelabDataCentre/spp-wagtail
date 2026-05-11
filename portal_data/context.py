"""Shared template context builders for the portal_data app."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from .services import get_dataset_listing, get_datatype_config


def positive_int(value: str | None, default: int) -> int:
    """Parse a positive integer from a query parameter."""
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        return default

    return max(parsed, 1)


def build_portal_data_context(
    request: HttpRequest,
    *,
    datatype: str,
    default_size: int = 25,
) -> dict[str, Any]:
    """Build the listing context shared by Django views and Wagtail pages."""

    config = get_datatype_config(datatype)

    if config is None:
        return {
            "datatype": datatype,
            "datatype_label": datatype,
            "error": f"Unknown data type: {datatype}",
            "query": "",
            "filters": {},
            "facets": {},
            "has_facets": False,
            "items": [],
            "total": 0,
            "page_number": 1,
            "size": default_size,
        }

    query = request.GET.get("q", "").strip()
    page_number = positive_int(request.GET.get("page"), 1)
    size = positive_int(request.GET.get("size"), default_size)

    facet_names = request.GET.getlist("facet") or list(config.default_facets)
    filters = {
        field: request.GET.getlist(field)
        for field in facet_names
        if request.GET.getlist(field)
    }

    listing = get_dataset_listing(
        datatype=datatype,
        query=query,
        filters=filters,
        facet_names=facet_names,
    )

    filtered_items = listing["items"]
    start = (page_number - 1) * size
    end = start + size

    return {
        "datatype": datatype,
        "datatype_label": config.label,
        "query": query,
        "filters": filters,
        "facets": listing["facets"],
        "has_facets": listing["has_facets"],
        "items": filtered_items[start:end],
        "total": len(filtered_items),
        "page_number": page_number,
        "size": size,
    }