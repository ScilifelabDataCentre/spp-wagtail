"""HTMX endpoint for data-table partial updates inside Wagtail pages."""

from __future__ import annotations

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from wagtail.models import Page

from cms.services.data_table import extract_table_data, get_table_context


def table_partial(request: HttpRequest, page_pk: int, table_id: str) -> HttpResponse:
    """Return the swappable table-content partial for a specific DataTableBlock.

    Called by HTMX when the user searches, pages, or changes the per-page
    selector on a ``DataTableBlock`` embedded in a Wagtail page's StreamField.

    Args:
        request:  The HTMX GET request carrying ``search``, ``per_page``,
                  and ``page`` query parameters.
        page_pk:  Primary key of the Wagtail page that owns the table.
        table_id: The ``table_id`` value of the target ``DataTableBlock``.

    Raises:
        Http404: If the page or table block cannot be found.
    """
    page = get_object_or_404(Page.objects.live().specific(), pk=page_pk)

    headers, rows, block_value = _find_table_block(page, table_id)

    ctx = get_table_context(
        request=request,
        rows=rows,
        headers=headers,
        table_url=request.path,
        table_id=table_id,
        table_label=block_value.get("table_label", ""),
        per_page_default=int(block_value.get("per_page", 10)),
        show_controls=bool(block_value.get("show_controls", False)),
    )
    return render(request, "cms/components/data_table_content.html", {"t": ctx})


def _find_table_block(
    page: Page, table_id: str
) -> tuple[list[str], list[list], dict]:
    """Locate a DataTableBlock in the page's ``content`` StreamField.

    Returns:
        A 3-tuple of ``(headers, rows, block_value)`` for the matched block.

    Raises:
        Http404: If no ``data_table`` block with *table_id* exists on the page.
    """
    content = getattr(page, "content", None)
    if content is None:
        raise Http404

    for block in content:
        if block.block_type == "data_table" and block.value.get("table_id") == table_id:
            headers, rows = extract_table_data(block.value["table"])
            return headers, rows, block.value

    raise Http404
