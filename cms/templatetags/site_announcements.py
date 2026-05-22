"""Template tags and filters for rendering site-wide announcement banners."""

import structlog
from django import template
from django.db.models.query import QuerySet

from cms.snippets import SiteAnnouncement

LOGGER = structlog.get_logger(__name__)

register = template.Library()

_EXTERNAL_HREF_PREFIXES = ("http://", "https://", "//")
_REQUIRED_REL_TOKENS = ("noopener", "noreferrer")


@register.simple_tag
def get_site_announcements() -> QuerySet[SiteAnnouncement]:
    """Return enabled site announcements ordered by ``sort_order``.

    Intended for use in the component partial that renders the announcement
    region above the site header. On any database or ORM error a warning is
    logged and an empty queryset is returned so template rendering stays
    resilient — a failure fetching announcements must never break the page.

    Returns:
        QuerySet[SiteAnnouncement]: Enabled announcements ordered by
            ``sort_order`` ascending. Empty on error.
    """

    try:
        return SiteAnnouncement.objects.filter(is_enabled=True).order_by("sort_order", "-pk")
    except Exception as e:
        LOGGER.warning(f"Problem fetching site announcements:\n{e}")
        return SiteAnnouncement.objects.none()
