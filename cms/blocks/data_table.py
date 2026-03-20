"""Data table StreamField block backed by TypedTableBlock."""

from __future__ import annotations

from typing import Any

from django.core.validators import RegexValidator
from django.urls import reverse
from wagtail import blocks
from wagtail.contrib.typed_table_block.blocks import TypedTableBlock

from cms.services.data_table import extract_table_data, get_table_context


class DataTableBlock(blocks.StructBlock):
    """Interactive data table with optional search and pagination.

    Wraps a ``TypedTableBlock`` so editors get a spreadsheet-style grid in the
    Wagtail admin while the front end renders the portal's DaisyUI + HTMX data
    table component.

    Attributes:
        table_id:      Unique identifier (per page) used as the HTML ``id``
                       prefix and HTMX target discriminator.
        table_label:   Human-readable ``aria-label`` for screen readers.
        show_controls: Toggle search bar, per-page selector, and pagination.
        per_page:      Default number of rows visible before pagination.
        table:         The actual tabular data, entered via TypedTableBlock.
    """

    table_id = blocks.CharBlock(
        required=True,
        max_length=60,
        validators=[RegexValidator(r"^[a-zA-Z0-9-]+$", "Only letters, numbers, and hyphens.")],
        help_text="Unique identifier for this table on the page — must not repeat if multiple tables are added (letters, numbers, hyphens).",
    )
    table_label = blocks.CharBlock(
        required=True,
        max_length=200,
        help_text="Accessible label for screen readers.",
    )
    show_controls = blocks.BooleanBlock(
        required=False,
        default=False,
        help_text="Show search, pagination, and per-page controls.",
    )
    per_page = blocks.ChoiceBlock(
        choices=[("10", "10"), ("25", "25"), ("50", "50")],
        default="10",
        help_text="Default number of rows per page.",
    )
    table = TypedTableBlock(
        [
            ("text", blocks.CharBlock()),
            ("rich_text", blocks.RichTextBlock(features=["bold", "italic", "link"])),
            ("numeric", blocks.FloatBlock()),
        ],
    )

    def get_context(self, value: dict[str, Any], parent_context: dict | None = None) -> dict:
        """Build the ``t`` context dict expected by the data-table templates."""
        # Extract before super() because Block.get_context mutates
        # parent_context in place, overwriting the "self" key with the
        # block value dict.
        request = parent_context.get("request") if parent_context else None
        page = (
            (parent_context.get("page") or parent_context.get("self"))
            if parent_context
            else None
        )

        context = super().get_context(value, parent_context)

        headers, rows = extract_table_data(value["table"])

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
            table_url=table_url,
            table_id=value["table_id"],
            table_label=value.get("table_label", ""),
            per_page_default=int(value.get("per_page", 10)),
            show_controls=bool(value.get("show_controls", False)),
        )
        context["t"] = table_ctx
        return context

    class Meta:
        """Set meta values."""

        icon = "table"
        label = "Data Table"
        template = "cms/blocks/data_table.html"
