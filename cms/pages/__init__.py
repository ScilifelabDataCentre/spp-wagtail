"""Wagtail CMS Page models."""

from .catalogue import CataloguePage
from .dashboard import DashboardPage, DashboardTopic
from .dashboard_index import DashboardIndexPage
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
    "DashboardIndexPage",
    "DashboardPage",
    "DashboardTopic",
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
