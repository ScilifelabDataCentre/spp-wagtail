"""Wagtail CMS Page models."""

from .catalogue import CataloguePage
from .highlights_and_editorials import (
    HighlightsAndEditorialsIndexPage,
    HighlightsAndEditorialsPage,
    HighlightsAndEditorialsTopic,
)
from .home import HomePage
from .outbreaks import OutbreakPage, OutbreaksIndexPage
from .section_index import SectionIndexPage
from .standard_page import StandardPage
from .topics import TopicPage, TopicsIndexPage

__all__ = [
    "CataloguePage",
    "HighlightsAndEditorialsIndexPage",
    "HighlightsAndEditorialsPage",
    "HighlightsAndEditorialsTopic",
    "HomePage",
    "OutbreakPage",
    "OutbreaksIndexPage",
    "SectionIndexPage",
    "StandardPage",
    "TopicPage",
    "TopicsIndexPage",
]
