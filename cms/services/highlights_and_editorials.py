"""Highlights and Editorials page service functions."""

from typing import Any

from django.http import Http404
from django.http.request import QueryDict
from django.utils.text import slugify


def get_related_articles(article, limit: int = 3, threshold: float = 0.1) -> list:  # noqa: ANN001
    """Get related articles based on keyword similarity.

    Finds articles with similar keywords using Jaccard similarity algorithm.
    Only considers articles of the same type (Data Highlight or Editorial).
    Considers all related articles regardless of creation date (past and future).
    Results are ordered by similarity score (highest first).

    Args:
        article: The main article for which to find related articles, it should be an
            instance of HighlightsAndEditorialsPage.
        limit: Maximum number of related articles to return (default: 3)
        threshold: Minimum similarity threshold between 0.0 and 1.0 (default: 0.1)

    Returns:
        List of related articles ordered by similarity score

    Example:
        Get top 3 related articles with at least 20% similarity:

        .. code-block:: python

            related_articles = get_related_articles(article, limit=3, threshold=0.2)
            for related_article in related_articles:
                print(related_article.title)

    """
    article_model = article.specific.__class__

    if not article.keyword_list:
        return article_model.objects.none()

    # Get all active articles of the same type, excluding current article
    candidate_articles = (
        article_model.objects.live()
        .filter(article_type=article.article_type)
        .exclude(id=article.id)
        .order_by("-first_published_at")
    )

    if not candidate_articles.exists():
        return article_model.objects.none()

    # Calculate similarity scores efficiently
    related_articles = []
    current_keywords = set(article.keyword_list)

    # Process articles in batches to avoid memory issues
    for article in candidate_articles.iterator(chunk_size=50):
        if not article.keywords:  # Skip articles without keywords
            continue

        article_keywords = set(article.keyword_list)

        # Calculate Jaccard similarity (intersection over union)
        intersection = len(current_keywords.intersection(article_keywords))
        union = len(current_keywords.union(article_keywords))
        if union == 0:
            continue

        similarity = intersection / union

        if similarity >= threshold:
            related_articles.append((article, similarity))

            # Early termination if we have enough high-similarity results
            if len(related_articles) >= limit * 2:
                break

    # Sort by similarity (highest first) and return limited results
    related_articles.sort(key=lambda x: x[1], reverse=True)
    return [article for article, _ in related_articles[:limit]]


SEARCH_MAX_LENGTH = 100


def validate_filters(
    querydict: QueryDict,
    valid_topics: list[str] | None = None,
    valid_types: list[str] | None = None,
    search_max_length: int = SEARCH_MAX_LENGTH,
) -> dict[str, Any]:
    """Validate article filter query parameters.

    Ensures that:
        - only allowed query parameters are present
        - search input length is reasonable
        - list-based filters are bounded in size
        - individual values are not excessively large

    Args:
        querydict: Incoming request query parameters (typically ``request.GET``).
        valid_topics: A list of allowed topic values.
        valid_types: A list of allowed article type values.
        search_max_length: Maximum allowed length for the search query.

    Returns:
        A normalized dictionary containing validated filter values.

    Raises:
        Http404: If invalid or unexpected query parameters are detected.

    Example:
        .. code-block:: python

            filters = validate_filters(request.GET)
    """

    validated_filters = {"search": "", "topic": [], "type": []}

    if not querydict:
        return validated_filters

    # Reject unexpected parameters
    for key in querydict:
        if key not in validated_filters:
            raise Http404(f"Invalid query parameter: {key}")

    # Validate search
    search = querydict.get("search", "").strip().lower()
    if len(search) > search_max_length:
        raise Http404("Search query too long")
    validated_filters["search"] = search

    # Validate article types
    types = querydict.getlist("type")
    if valid_types and any(article_type not in map(slugify, valid_types) for article_type in types):
        raise Http404("Invalid article type value")
    if valid_types and len(types) > len(valid_types):
        raise Http404("Too many article types selected")
    validated_filters["type"] = types

    # Validate topics
    topics = querydict.getlist("topic")
    if valid_topics and any(topic not in map(slugify, valid_topics) for topic in topics):
        raise Http404("Invalid topic value")
    if valid_topics and len(topics) > len(valid_topics):
        raise Http404("Too many topics selected")
    validated_filters["topic"] = topics

    return validated_filters
