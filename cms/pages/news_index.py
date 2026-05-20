"""CMS Page for News."""

from typing import Any

from django.http import HttpRequest
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.fields import StreamField
from wagtail.models import Page

from cms.blocks import AlertBlock


class NewsIndexPage(Page):
    """A page listing all news articles.

    This page is intended to be used as a parent page for NewsPage instances.
    Only one instance of this page can exist. Child news pages will be listed
    as cards on this page.

    Attributes:
        content (StreamField): A stream field for the page content, allowing rich text.
    """

    max_count = 1
    template = "cms/pages/news_index.html"
    parent_page_types = ["cms.HomePage"]
    subpage_types = ["cms.NewsPage"]

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
        """Add child news articles to the context."""
        from cms.pages.news import NewsPage

        context = super().get_context(request)
        context["all_news"] = (
            self.get_children()
            .type(NewsPage)
            .live()
            .public()
            .specific()
            .order_by("-first_published_at")
        )
        return context
