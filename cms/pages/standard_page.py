"""A standard page model."""

from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page


class StandardPage(Page):
    """A standard base page with rich text, images, and call-to-action blocks.

    This page type serves as a simple content page with a StreamField
    that supports a few commonly used content blocks. It cannot have
    any child pages and can only be added under certain parent pages.

    Attributes:
        content (StreamField): StreamField with multiple content block types:
            - RichTextBlock: formatted text (headings, bold, italic, links, lists)
    """

    template = "cms/pages/standard_page.html"
    parent_page_types = ["cms.HomePage", "cms.SectionIndexPage"]
    subpage_types = []  # no child page allowed

    content = StreamField(
        [
            (
                "text",
                blocks.RichTextBlock(
                    features=["h2", "h3", "bold", "italic", "link", "ol", "ul"],
                    verbose_name="Text (Rich)",
                ),
            ),
        ],
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("content"),
    ]
