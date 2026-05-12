"""CMS Page for News."""

from typing import Any

from django.db import models
from django.http import HttpRequest
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.fields import StreamField
from wagtail.images import get_image_model_string
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
        context = super().get_context(request)
        context["all_news"] = (
            self.get_children().type(NewsPage).live().specific().order_by("-first_published_at")
        )
        return context


class NewsPage(Page):
    """A page representing a single news article.

    This page is intended to be a child of NewsIndexPage. It contains the
    content of a news article, which can include rich text and alerts.

    Attributes:
        description (str): A brief text summary that will be displayed on the news card.
        image (Image): A thumbnail image that will be displayed on the news card.
        content (StreamField): A stream field for the news article content, allowing rich text.
    """

    template = "cms/pages/news.html"
    parent_page_types = ["cms.NewsIndexPage"]
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
        blank=True,
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel(
                    "description",
                    help_text="Brief text summary that will be displayed on the news card.",
                ),
                FieldPanel(
                    "image",
                    help_text="Thumbnail image that will be displayed on the news card.",
                ),
            ],
            heading="Card details",
        ),
        FieldPanel("content", help_text="The main content for the news article."),
    ]

    promote_panels = Page.promote_panels + [
        FieldPanel(
            "first_published_at",
            help_text=(
                "The page creation date that will be displayed on the card. "
                "Defaults to the publication date."
            ),
        ),
    ]

    def get_context(self, request: HttpRequest) -> dict[str, Any]:
        """Add the parent page's title to the context for display on the news page."""
        context = super().get_context(request)
        parent = self.get_parent().specific
        if parent and isinstance(parent, NewsIndexPage):
            context["page_heading"] = parent.title
            context["parent_page"] = parent.url
        return context
