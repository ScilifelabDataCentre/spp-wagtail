"""CMS pages for highlights and editorials."""

from collections.abc import Iterator
from typing import Any

from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.http import urlencode
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, PageChooserPanel
from wagtail.blocks import RichTextBlock
from wagtail.fields import RichTextField, StreamField
from wagtail.images import get_image_model_string
from wagtail.models import Orderable, Page

from cms.blocks import AlertBlock
from cms.services.highlights_and_editorials import get_related_articles, validate_filters

ARTICLE_TYPE_CHOICES = [
    ("data-highlight", "Data Highlight"),
    ("editorial", "Editorial"),
]


class HighlightsAndEditorialsIndexPage(Page):
    """A page listing all highlights and editorials.

    This page is intended to be used as a parent page for HighlightsAndEditorialsPage instances.
    Only one instance of this page can exist. Child pages will be listed as cards on this page.

    Attributes:
        content (StreamField): A stream field for the page content, allowing rich text.
    """

    max_count = 1
    template = "cms/pages/highlights_and_editorials_index.html"
    parent_page_types = ["cms.HomePage"]
    subpage_types = ["cms.HighlightsAndEditorialsPage"]

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
        """Add child highlights and editorials to the context."""

        context = super().get_context(request)

        # Collect all unique topics from the child articles for filtering options
        context["all_topics"] = sorted(
            HighlightsAndEditorialsTopic.objects.filter(page__live=True)
            .values_list("topic__title", flat=True)
            .distinct()
        )
        # Collect article types labels for filtering options
        context["all_article_types"] = sorted([label for _, label in ARTICLE_TYPE_CHOICES])

        # Validate and clean the query parameters for filtering
        validated_filters = validate_filters(
            request.GET,
            valid_topics=context["all_topics"],
            valid_types=context["all_article_types"],
        )

        filters = models.Q()

        # If a search query is passed as a query parameter, filter the articles based on that query
        search_filter = validated_filters.get("search")
        if search_filter:
            filters &= (
                models.Q(title__icontains=search_filter)
                | models.Q(description__icontains=search_filter)
                | models.Q(keywords__icontains=search_filter)
            )

        # If an article type is passed as a query parameter, filter the articles based on that type
        type_filter = validated_filters.get("type")
        if type_filter:
            filters &= models.Q(article_type__in=type_filter)
            context["type_filter"] = type_filter

        # If a topic is passed as a query parameter, filter the articles based on that topic
        topics_filter = validated_filters.get("topic")
        if topics_filter:
            filters &= models.Q(article_topics__topic__slug__in=topics_filter)
            context["topics_filter"] = topics_filter

        # Add the articles to the context, applying the filters and ensuring distinct results
        context["articles_list"] = (
            HighlightsAndEditorialsPage.objects.child_of(self)
            .live()
            .prefetch_related("article_topics__topic")
            .order_by("-first_published_at")
            .distinct()
            .filter(filters)
        )

        return context

    def serve(self, request: HttpRequest) -> HttpResponse:
        """Override serve method to handle HTMX requests for filtering."""
        if request.htmx:
            # Clean the URL by removing the search parameter for HTMX requests
            # to prevent it from being added to the browser URL.
            query = request.GET.copy()
            query.pop("search", None)
            clean_url = f"{request.path}?{urlencode(query, doseq=True)}" if query else request.path

            # For HTMX requests, we only want to return the articles list part of the page
            response = render(
                request,
                "cms/components/highlights_and_editorials_list.html#articles_grid",
                self.get_context(request),
            )
            response["HX-Replace-Url"] = clean_url
            return response
        else:
            return super().serve(request)


class HighlightsAndEditorialsTopic(Orderable):
    """A model representing the many-to-many relationship.

    This model represents the many-to-many relationship between highlights/editorials and topics.

    Attributes:
    page (ParentalKey): The highlight or editorial page that this topic is associated with.
    topic (ForeignKey): The topic that is associated with the highlight or editorial.
    """

    page = ParentalKey(
        "cms.HighlightsAndEditorialsPage",
        on_delete=models.CASCADE,
        related_name="article_topics",
    )
    topic = models.ForeignKey("cms.TopicPage", on_delete=models.CASCADE)

    panels = [
        PageChooserPanel("topic", "cms.TopicPage"),
    ]

    class Meta:
        """Meta options for the HighlightsAndEditorialsTopic model."""

        verbose_name = "Related Topic"
        verbose_name_plural = "Related Topics"


class HighlightsAndEditorialsPage(Page):
    """A page representing a single highlight or editorial.

    This page is intended to be a child of HighlightsAndEditorialsIndexPage.
    It will be displayed as a card on the index page.

    Attributes:
        description (str): A brief description of the highlight or editorial.
        image (ForeignKey): An image associated with the highlight or editorial
            (actually saved as a foreign key).
        image_caption (str): An optional caption for the image.
        article_type (str): The type of the article, either "data_highlight" or "editorial".
        announcement (str): An optional announcement message for the article,
            supporting basic rich text formatting.
        keywords (str): An optional comma-separated string of keywords for related content
            matching and search.
        author (str): An optional author name or names for the article.
        content (StreamField): A stream field for the page content, allowing rich text.
    """

    template = "cms/pages/highlights_and_editorials.html"
    parent_page_types = ["cms.HighlightsAndEditorialsIndexPage"]
    subpage_types = []

    description = models.CharField(max_length=255, blank=False)
    image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=False,
        on_delete=models.PROTECT,
        related_name="+",
    )
    image_caption = models.CharField(max_length=255, blank=True)
    article_type = models.CharField(
        max_length=50,
        blank=False,
        choices=ARTICLE_TYPE_CHOICES,
    )
    announcement = RichTextField(features=["bold", "italic", "link", "ol", "ul"], blank=True)
    keywords = models.TextField(blank=True)
    author = models.CharField(max_length=255, blank=True)
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
                    help_text=(
                        "Brief text summary that will be displayed on the highlights "
                        "and editorials card."
                    ),
                ),
                FieldPanel(
                    "image",
                    help_text=(
                        "Thumbnail image that will be displayed on the highlights "
                        "and editorials card."
                    ),
                ),
                FieldPanel(
                    "image_caption",
                    help_text=(
                        "Optional caption for the thumbnail image. Displayed on the "
                        "article page but not on the card."
                    ),
                ),
            ],
            heading="Card details",
        ),
        FieldPanel(
            "article_type",
            help_text=("The type of the article i.e., highlight or editorial."),
        ),
        InlinePanel(
            "article_topics",
            classname="collapsed",
            help_text="Research topics associated with this highlight or editorial.",
        ),
        MultiFieldPanel(
            [
                FieldPanel(
                    "announcement",
                    help_text=(
                        "Optional announcement message supported by basic rich text formatting. "
                        "Displayed prominently at the top of the page, above the main content."
                    ),
                ),
                FieldPanel(
                    "keywords",
                    help_text=("Comma-separated keywords for related content matching and search"),
                ),
                FieldPanel(
                    "author",
                    help_text=(
                        "Optional author name or names for the article. "
                        "Displayed on the article page but not used for search or filtering."
                    ),
                ),
            ],
            heading="Optional metadata",
            classname="collapsed",
        ),
        FieldPanel(
            "content",
            help_text="The main content for the highlights and editorials page.",
        ),
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

    @property
    def topics(self) -> Iterator:
        """Return a sorted list of topics associated with this article."""
        return sorted((rel.topic for rel in self.article_topics.all()), key=lambda t: t.title)

    @property
    def keyword_list(self) -> list[str]:
        """Return keywords as a list of cleaned strings."""
        if not self.keywords.strip():
            return []
        return [tag.strip().lower() for tag in self.keywords.split(",") if tag.strip()]

    def get_context(self, request: HttpRequest) -> dict[str, Any]:
        """Add the parent page's title to the context for display on the page."""
        context = super().get_context(request)
        context["page_heading"] = self.get_parent().specific.title
        context["related_articles"] = get_related_articles(self)
        return context
