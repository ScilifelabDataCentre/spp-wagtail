"""Shared template context builders for the portal_data app."""

from __future__ import annotations

from typing import Any

from django.core.paginator import Paginator
from django.http import HttpRequest

from .services import get_dataset_listing, get_datatype_config

DEFAULT_SIZE = 25
DEFAULT_SIZE_OPTIONS: tuple[int, ...] = (25, 50, 100)


def positive_int(value: str | None, default: int) -> int:
    """Parse a positive integer from a query parameter."""
    try:
        parsed = int(value or default)
    except (TypeError, ValueError) as err:
        return default

    return max(parsed, 1)


def normalize_datatype(value: object) -> str:
    """Normalise datatype values coming from URLs, Wagtail fields, or tests."""
    return str(value or "").strip().lower()


def _facet_label(field: str) -> str:
    """Convert a field name like 'design_types' to a readable label 'Design Types'."""
    return field.replace("_", " ").title()


def _build_facet_list(
    raw_facets: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Convert the raw {field: buckets} dict to a list of dicts for the template.

    Each item exposes:
      - field:   the raw field name used as the checkbox <input name>
      - label:   a human-readable display label
      - buckets: the list of value/count/checked dicts
    """
    return [
        {"field": field, "label": _facet_label(field), "buckets": buckets}
        for field, buckets in raw_facets.items()
    ]


def build_portal_data_context(
    request: HttpRequest,
    *,
    datatype: object,
    default_size: int = DEFAULT_SIZE,
    size_options: tuple[int, ...] = DEFAULT_SIZE_OPTIONS,
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
            "facets": [],
            "has_facets": False,
            "items": [],
            "total": 0,
            "page_obj": None,
            "page_range": [],
            "size": default_size,
            "size_options": size_options,
            "form_action": request.path,
            "reset_url": request.path,
            "pagination_query": "",
        }

    query = request.GET.get("q", "").strip()
    page_number = positive_int(request.GET.get("page"), 1)

    raw_size = request.GET.get("size", default_size)
    try:
        size = int(raw_size)
    except (TypeError, ValueError) as err:
        size = default_size

    if size not in size_options:
        size = default_size

    # Facet fields are configuration, not request state.
    #
    # Previously, facet_names came from request.GET.getlist("facet"), with a fallback
    # to config.default_facets. That made the UI depend on hidden "facet" inputs.
    #
    # With HTMX, the form submits selected facet values directly via checkbox names
    # such as ?year=2024&repository=MetaboLights. The list of available facet groups
    # should therefore always come from the backend config.
    facet_names = list(config.default_facets)

    filters = {
        field: request.GET.getlist(field) for field in facet_names if request.GET.getlist(field)
    }

    listing = get_dataset_listing(
        datatype=datatype,
        query=query,
        filters=filters,
        facet_names=facet_names,
    )

    # Transform the raw {field: buckets} dict into a template-friendly list of dicts
    # so the template can access both the field name (for checkbox names) and a
    # formatted display label without needing a custom template tag.
    facets = _build_facet_list(listing["facets"])

    paginator = Paginator(listing["items"], size)
    page_obj = paginator.get_page(page_number)
    page_range = [
        None if p == Paginator.ELLIPSIS else p
        for p in paginator.get_elided_page_range(
            page_obj.number,
            on_each_side=2,
            on_ends=1,
        )
    ]

    # Used by pagination links so search and selected facets survive page changes.
    # We intentionally remove "page" because each pagination link supplies its own.
    query_params = request.GET.copy()
    query_params.pop("page", None)
    pagination_query = query_params.urlencode()

    return {
        "datatype": datatype,
        "raw_datatype": raw_datatype,
        "datatype_label": config.label,
        "query": query,
        "filters": filters,
        "facet_names": facet_names,
        "facets": facets,
        "has_facets": listing["has_facets"],
        "items": page_obj.object_list,
        "total": paginator.count,
        "page_obj": page_obj,
        "page_range": page_range,
        "size": size,
        "size_options": size_options,
        "form_action": request.path,
        "reset_url": request.path,
        "pagination_query": pagination_query,
    }
