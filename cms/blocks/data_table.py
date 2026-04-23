"""Data table StreamField block backed by TypedTableBlock."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.urls import reverse
from django.utils.text import slugify
from wagtail import blocks
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.contrib.typed_table_block.blocks import TypedTableBlock

from cms.services.data_table import (
    DEFAULT_PER_PAGE,
    DEFAULT_PER_PAGE_OPTIONS,
    extract_block_params,
    extract_table_data,
    get_table_context,
)


class DataTableBlock(blocks.StructBlock):
    """Interactive data table with optional search and pagination.

    Wraps a ``TypedTableBlock`` so editors get a spreadsheet-style grid in the
    Wagtail admin while the front end renders the portal's DaisyUI + HTMX data
    table component.

    The built-in TypedTableBlock *Caption* field is required and rendered as a
    visible heading above the table; it also provides the accessible label
    referenced by ``aria-labelledby`` on the ``<table>`` element.

    Attributes:
        table_id:      Unique identifier (per page) used as the HTML ``id``
                       prefix and HTMX target discriminator.  Auto-generated
                       from the table caption when left blank.
        show_controls: Toggle search bar, per-page selector, and pagination.
        per_page:      Default number of rows visible before pagination.
        table:         The actual tabular data, entered via TypedTableBlock.
    """

    table_id = blocks.CharBlock(
        required=False,
        max_length=60,
        validators=[RegexValidator(r"^[a-zA-Z0-9-]*$", "Only letters, numbers, and hyphens.")],
        help_text=(
            "Unique identifier for this table on the page (letters, numbers, "
            "hyphens). Defaults to a slugified version of the table caption."
        ),
    )
    show_controls = blocks.BooleanBlock(
        required=False,
        default=False,
        help_text="Show search, pagination, and per-page controls.",
    )
    per_page = blocks.ChoiceBlock(
        choices=[(str(v), str(v)) for v in DEFAULT_PER_PAGE_OPTIONS],
        default=str(DEFAULT_PER_PAGE),
        required=False,
        help_text=(
            "Number of rows per page when controls are visible "
            "(display all entries if controls are not shown)."
        ),
    )
    table = TypedTableBlock(
        [
            ("text", blocks.CharBlock()),
            ("rich_text", blocks.RichTextBlock(features=["bold", "italic", "link"])),
            ("numeric", blocks.FloatBlock()),
            ("integer", blocks.IntegerBlock()),
        ],
    )

    def clean(self, value: dict[str, Any]) -> dict[str, Any]:
        """Require a non-empty caption and auto-fill table_id from it when blank."""
        cleaned = super().clean(value)
        table = cleaned.get("table")
        caption = (getattr(table, "caption", "") or "").strip() if table else ""
        if not caption:
            raise StructBlockValidationError(
                block_errors={"table": ValidationError("Table caption is required.")},
            )
        if not cleaned.get("table_id"):
            cleaned["table_id"] = slugify(caption)[:60]
        return cleaned

    def get_context(self, value: dict[str, Any], parent_context: dict | None = None) -> dict:
        """Build the ``t`` context dict expected by the data-table templates."""
        request = parent_context.get("request") if parent_context else None
        page = (
            (parent_context.get("page") or parent_context.get("self")) if parent_context else None
        )

        context = super().get_context(value, parent_context)

        headers, rows, caption = extract_table_data(value["table"])

        table_url = ""
        if page and hasattr(page, "pk"):
            table_url = reverse(
                "cms:table_partial",
                kwargs={"page_pk": page.pk, "table_id": value["table_id"]},
            )

        table_ctx = get_table_context(
            request=request,
            rows=rows,
            headers=headers,
            caption=caption,
            table_url=table_url,
            **extract_block_params(value),
        )
        context["t"] = table_ctx
        return context

    class Meta:
        """Set meta values."""

        icon = "table"
        label = "Data Table"
        template = "cms/blocks/data_table.html"
