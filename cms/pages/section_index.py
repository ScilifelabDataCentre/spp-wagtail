"""A section index page model."""

from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.fields import StreamField
from wagtail.models import Page


class SectionIndexPage(Page):
    """Generic section landing page.

    Acts as a navigational grouping under the homepage.
    Allowed children:
        - ``StandardPage``

    Attributes:
        content (StreamField): Rich text content for the section.
    """

    template = "cms/pages/section_index.html"
    parent_page_types = ["cms.HomePage"]
    subpage_types = ["cms.StandardPage"]

    content = StreamField(
        [
            (
                "text",
                RichTextBlock(
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
