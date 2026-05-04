"""CMS pages for topics."""

from typing import Any

from django.db import models
from django.http import HttpRequest
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.fields import StreamField
from wagtail.images import get_image_model_string
from wagtail.models import Page

from cms.blocks import AlertBlock


class TopicsIndexPage(Page):
    """A page listing all topics.

    This page is intended to be used as a parent page for TopicPage instances.
    Only one instance of this page can exist. Child topic pages will be listed
    as cards on this page.

    Attributes:
        content (StreamField): A stream field for the page content, allowing rich text.
    """

    max_count = 1
    template = "cms/pages/topics_index.html"
    parent_page_types = ["cms.HomePage"]
    subpage_types = ["cms.TopicPage"]

    content = StreamField(
        [
            ("text", RichTextBlock()),
            ("alert", AlertBlock()),
        ],
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("content"),
    ]

    def get_context(self, request: HttpRequest) -> dict[str, Any]:
        """Add child topics to the context."""
        context = super().get_context(request)
        context["topics"] = self.get_children().type(TopicPage).live().specific().order_by("title")
        return context


class TopicPage(Page):
    """A page representing a single topic.

    This page is intended to be used as a child of TopicsIndexPage. It represents
    a single topic and can contain content related to that topic.

    Attributes:
        description (str): A brief description of the topic.
        image (ForeignKey): An image associated with the topic (actually saved as a foreign key).
        content (StreamField): A stream field for the page content, allowing rich text.
    """

    template = "cms/pages/topic.html"
    parent_page_types = ["cms.TopicsIndexPage"]
    subpage_types = []

    description = models.CharField(max_length=255, blank=False)
    image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=False,
        on_delete=models.PROTECT,
        related_name="+",
    )
    content = StreamField(
        [
            ("text", RichTextBlock()),
            ("alert", AlertBlock()),
        ],
        blank=False,
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel(
                    "description",
                    help_text="Brief text summary that will be displayed on the topics card.",
                ),
                FieldPanel(
                    "image",
                    help_text="Thumbnail image that will be displayed on the topics card.",
                ),
            ],
            heading="Card details",
        ),
        FieldPanel(
            "content",
            help_text="The main content for the topic page.",
        ),
    ]

    def get_context(self, request: HttpRequest) -> dict[str, Any]:
        """Add the parent page's title to the context for display on the topic page."""
        context = super().get_context(request)
        context["page_heading"] = self.get_parent().specific.title
        return context
