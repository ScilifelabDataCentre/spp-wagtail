"""Wagtail CMS Page models."""

from .catalogue import CataloguePage
from .highlights_and_editorials import (
    HighlightsAndEditorialsPage,
    HighlightsAndEditorialsTopic,
)
from .highlights_and_editorials_index import HighlightsAndEditorialsIndexPage
from .home import HomePage
from .outbreaks import OutbreakPage, OutbreaksIndexPage
from .portal_data import PortalDataPage
from .section_index import SectionIndexPage
from .standard_page import StandardPage
from .topics import TopicPage
from .topics_index import TopicsIndexPage

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
