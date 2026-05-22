"""Wagtail CMS Page models."""

from .catalogue import CataloguePage
from .highlights_and_editorials import (
    HighlightsAndEditorialsIndexPage,
    HighlightsAndEditorialsPage,
    HighlightsAndEditorialsTopic,
)
from .home import HomePage
from .outbreaks import OutbreakPage, OutbreaksIndexPage
from .portal_data import PortalDataPage
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
    "PortalDataPage",
    "SectionIndexPage",
    "StandardPage",
    "TopicPage",
    "TopicsIndexPage",
]
