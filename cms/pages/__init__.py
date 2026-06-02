"""Wagtail CMS Page models."""

from .catalogue import CataloguePage
from .dashboard import DashboardPage
from .dashboard_index import DashboardIndexPage
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
from .plp_index import PlpIndexPage
from .plp_project import PlpProjectPage
from .portal_data import PortalDataPage
from .outbreaks import OutbreakPage, OutbreaksIndexPage
from .section_index import SectionIndexPage
from .standard_page import StandardPage
from .topics import TopicPage
from .topics_index import TopicsIndexPage

__all__ = [
    "CataloguePage",
    "DashboardIndexPage",
    "DashboardPage",
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
    "OutbreaksIndexPage",
    "PortalDataPage",
    "SectionIndexPage",
    "StandardPage",
    "TopicPage",
    "TopicsIndexPage",
]

