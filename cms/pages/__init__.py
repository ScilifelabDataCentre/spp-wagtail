"""Wagtail CMS Page models."""

from .home import HomePage
from .outbreaks import OutbreakPage, OutbreaksIndexPage
from .section_index import SectionIndexPage
from .standard_page import StandardPage

__all__ = [
    "HomePage",
    "OutbreakPage",
    "OutbreaksIndexPage",
    "SectionIndexPage",
    "StandardPage",
]
