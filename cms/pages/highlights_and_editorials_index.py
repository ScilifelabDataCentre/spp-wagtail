"""CMS page for highlights and editorials index."""

from typing import Any

from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.http import urlencode
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.fields import StreamField
from wagtail.models import Page

from cms.blocks import AlertBlock
from cms.services.highlights_and_editorials import validate_filters


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

        # Importing here to avoid circular imports
        from cms.pages.highlights_and_editorials import (
            ARTICLE_TYPE_CHOICES,
            HighlightsAndEditorialsPage,
            HighlightsAndEditorialsTopic,
        )

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
            .public()
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
