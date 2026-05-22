"""Wagtail CMS Page models."""

from .catalogue import CataloguePage
from .highlights_and_editorials import (
    HighlightsAndEditorialsIndexPage,
    HighlightsAndEditorialsPage,
    HighlightsAndEditorialsTopic,
)
from .home import HomePage
from .news import NewsPage
from .news_index import NewsIndexPage
from .outbreaks import OutbreakPage, OutbreaksIndexPage
from .plp_index import PlpIndexPage
from .plp_project import PlpProjectPage
from .section_index import SectionIndexPage
from .standard_page import StandardPage
from .topics import TopicPage, TopicsIndexPage

__all__ = [
    "CataloguePage",
    "HighlightsAndEditorialsIndexPage",
    "HighlightsAndEditorialsPage",
    "HighlightsAndEditorialsTopic",
    "HomePage",
    "NewsIndexPage",
    "NewsPage",
    "OutbreakPage",
    "OutbreaksIndexPage",
    "PlpIndexPage",
    "PlpProjectPage",
    "SectionIndexPage",
    "StandardPage",
    "TopicPage",
    "TopicsIndexPage",
]
