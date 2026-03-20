"""HTMX endpoint for data-table partial updates inside Wagtail pages."""

from __future__ import annotations

from typing import Any

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from wagtail.models import Page

from cms.services.data_table import extract_block_params, extract_table_data, get_table_context


@require_GET
@cache_control(max_age=60)
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
        Http404: If the page or table block cannot be found, or if the
                 requesting user does not satisfy the page's view restrictions.
    """
    page = get_object_or_404(Page.objects.live().specific(), pk=page_pk)

    for restriction in page.get_view_restrictions():
        if not restriction.accept_request(request):
            raise Http404

    headers, rows, block_value = _find_table_block(page, table_id)

    ctx = get_table_context(
        request=request,
        rows=rows,
        headers=headers,
        table_url=request.path,
        **extract_block_params(block_value),
    )
    return render(request, "cms/components/data_table_content.html", {"t": ctx})


def _find_table_block(
    page: Page, table_id: str
) -> tuple[list[str], list[list[Any]], dict[str, Any]]:
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
