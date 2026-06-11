"""A home page model."""

from wagtail.models import Page


class HomePage(Page):
    """Top-level homepage of the site.

    This page sits directly under the Wagtail root node and serves as
    the main entry point for the website. It can only be created once.
    """

    template = "cms/pages/home.html"
    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
