"""Collapsible disclosure StructBlock for inline expandable content."""

from wagtail import blocks

from cms.blocks.data_table import DataTableBlock


class CollapsibleBlock(blocks.StructBlock):
    """Labelled, expandable section rendered as native ``<details>``/``<summary>``.

    Designed primarily for the PLP program timeline, but reusable on any page
    that needs an editor-managed disclosure widget. Editors choose a label
    shown in the always-visible summary line and fill the body with one or
    more inner blocks (rich text or data table).

    Attributes:
        label (CharBlock): Title shown inside the always-visible ``<summary>``.
        body (StreamBlock): One or more inner blocks (rich text or data
            table) revealed when the disclosure is opened. ``min_num=1``
            guarantees an empty body never validates.
    """

    label = blocks.CharBlock(
        required=True,
        max_length=255,
        help_text="Title shown in the always-visible summary line.",
    )
    body = blocks.StreamBlock(
        [
            ("text", blocks.RichTextBlock()),
            ("data_table", DataTableBlock()),
        ],
        min_num=1,
        help_text="Inner content revealed when the section is opened.",
    )

    class Meta:
        """Set meta values."""

        icon = "list-ul"
        label = "Collapsible"
        help_text = (
            "Labelled, expandable section using native <details>/<summary>. "
            "Use for timelines or other long-form content that should start collapsed."
        )
        template = "cms/blocks/collapsible.html"
