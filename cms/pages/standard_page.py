"""Standard content page model with a StreamField body."""

from django.db import models
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from cms.blocks import AlertBlock, CardBlock, CardGridBlock, ChildPageCardBlock, DataTableBlock


class StandardPage(Page):
    """Simple content page with a reorderable stream of common blocks.

    Cannot have child pages. Allowed parents: home or section index pages.

    Attributes:
        show_toc: Whether to generate and display a table of contents sidebar.
        content (StreamField): StreamField with multiple content block types:
            - RichTextBlock: formatted text (headings, bold, italic, links, lists)
            - DataTableBlock: interactive table with search and pagination
    """

    template = "cms/pages/standard_page.html"
    parent_page_types = ["cms.HomePage", "cms.SectionIndexPage"]
    subpage_types = []  # No child pages allowed.

    show_toc = models.BooleanField(default=False, blank=True, verbose_name="Show TOC")

    content = StreamField(
        [
            (
                "text",
                blocks.RichTextBlock(
                    verbose_name="Text (rich)",
                    help_text="Main body copy. Use headings for structure; images optional.",
                ),
            ),
            ("alert", AlertBlock()),
            ("card", CardBlock()),
            ("card_grid", CardGridBlock()),
            ("child_page_cards", ChildPageCardBlock()),
            ("data_table", DataTableBlock()),
        ],
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel(
            "content",
            help_text="Drag blocks to reorder. Each block type has its own fields and help text.",
        ),
    ]

    promote_panels = Page.promote_panels + [
        FieldPanel(
            "show_toc",
            help_text=(
                "If checked, a table of contents will be generated from "
                "headings in the content and displayed in a sidebar xx."
            ),
        ),
    ]
