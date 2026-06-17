"""CMS page for topics index."""

from typing import Any

from django.http import HttpRequest
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.fields import StreamField
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

        # Importing here to avoid circular import issues
        from cms.pages.topics import TopicPage

        context = super().get_context(request)
        context["topics"] = (
            self.get_children().type(TopicPage).live().public().specific().order_by("title")
        )
        return context
