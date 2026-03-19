"""A section index page model."""

from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.fields import StreamField
from wagtail.models import Page


# Dict to set allowed child page type for specific section type
SECTION_PAGE_TYPES = {
    "default": "cms.StandardPage",
}


class SectionIndexPage(Page):
    """Generic section page that restricts allowed child page types.

    Attributes:
        section_type (str): The type of this section, used to determine allowed child pages.
        content (StreamField): Rich text content for the section.
    """

    # List of available section types as (key, display_name) tuples.
    SECTION_TYPES = [(k, k.capitalize()) for k in SECTION_PAGE_TYPES]

    template = "cms/pages/section_index.html"
    parent_page_types = ["cms.HomePage"]
    subpage_types = list({*SECTION_PAGE_TYPES.values()})

    section_type = models.CharField(
        max_length=20,
        choices=SECTION_TYPES,
        default="default",
    )

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
        FieldPanel("section_type"),
        FieldPanel("content"),
    ]
