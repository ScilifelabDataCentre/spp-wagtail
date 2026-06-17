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


def normalize_datatype(value: object) -> str:
    """Normalise datatype values coming from URLs, Wagtail fields, or tests."""
    return str(value or "").strip().lower()


def build_portal_data_context(
    request: HttpRequest,
    *,
    datatype: object,
    default_size: int = 25,
) -> dict[str, Any]:
    """Build the listing context shared by Django views and Wagtail pages."""

    raw_datatype = datatype
    datatype = normalize_datatype(datatype)

    config = get_datatype_config(datatype)

    if config is None:
        return {
            "datatype": datatype,
            "raw_datatype": raw_datatype,
            "datatype_label": datatype or "Unknown",
            "error": f"Unknown data type: {datatype or raw_datatype}",
            "query": "",
            "filters": {},
            "facet_names": [],
            "facets": {},
            "has_facets": False,
            "items": [],
            "total": 0,
            "page_number": 1,
            "size": default_size,
            "form_action": request.path,
            "reset_url": request.path,
        }

    query = request.GET.get("q", "").strip()
    page_number = positive_int(request.GET.get("page"), 1)
    size = positive_int(request.GET.get("size"), default_size)

    facet_names = request.GET.getlist("facet") or list(config.default_facets)
    filters = {
        field: request.GET.getlist(field) for field in facet_names if request.GET.getlist(field)
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
        "raw_datatype": raw_datatype,
        "datatype_label": config.label,
        "query": query,
        "filters": filters,
        "facet_names": facet_names,
        "facets": listing["facets"],
        "has_facets": listing["has_facets"],
        "items": filtered_items[start:end],
        "total": len(filtered_items),
        "page_number": page_number,
        "size": size,
        "form_action": request.path,
        "reset_url": request.path,
    }
