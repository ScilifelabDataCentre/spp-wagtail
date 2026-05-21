"""Wagtail CMS Page models."""

from .highlights_and_editorials import (
    HighlightsAndEditorialsPage,
    HighlightsAndEditorialsTopic,
)
from .highlights_and_editorials_index import HighlightsAndEditorialsIndexPage
from .home import HomePage
from .news import NewsPage
from .news_index import NewsIndexPage
from .outbreaks import OutbreakPage
from .outbreaks_index import OutbreaksIndexPage
from .section_index import SectionIndexPage
from .standard_page import StandardPage
from .topics import TopicPage
from .topics_index import TopicsIndexPage

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
