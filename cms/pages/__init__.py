"""Wagtail CMS Page models."""

from .highlights_and_editorials import (
    HighlightsAndEditorialsIndexPage,
    HighlightsAndEditorialsPage,
    HighlightsAndEditorialsTopic,
)
from .home import HomePage
from .news import NewsPage
from .news_index import NewsIndexPage
from .outbreaks import OutbreakPage, OutbreaksIndexPage
from .section_index import SectionIndexPage
from .standard_page import StandardPage
from .topics import TopicPage, TopicsIndexPage

__all__ = [
    "HighlightsAndEditorialsIndexPage",
    "HighlightsAndEditorialsPage",
    "HighlightsAndEditorialsTopic",
    "HomePage",
    "NewsIndexPage",
    "NewsPage",
    "OutbreakPage",
    "OutbreaksIndexPage",
    "SectionIndexPage",
    "StandardPage",
    "TopicPage",
    "TopicsIndexPage",
]
