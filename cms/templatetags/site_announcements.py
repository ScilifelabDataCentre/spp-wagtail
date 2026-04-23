"""Template tags and filters for rendering site-wide announcement banners."""

import structlog
from bs4 import BeautifulSoup
from django import template
from django.db.models.query import QuerySet
from django.utils.safestring import SafeString, mark_safe

from cms.snippets import SiteAnnouncement

LOGGER = structlog.get_logger(__name__)

register = template.Library()

_EXTERNAL_HREF_PREFIXES: tuple[str, ...] = ("http://", "https://", "//")
_REQUIRED_REL_TOKENS: tuple[str, ...] = ("noopener", "noreferrer")


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
        return SiteAnnouncement.objects.filter(is_enabled=True).order_by("sort_order")
    except Exception as e:
        LOGGER.warning(f"Problem fetching site announcements:\n{e}")
        return SiteAnnouncement.objects.none()


@register.filter
def announcement_rich_text(value: str) -> SafeString:
    """Harden external ``<a>`` elements inside an announcement's rich text.

    For each anchor whose ``href`` targets an external origin — i.e. starts
    with ``http://``, ``https://``, or a protocol-relative ``//`` — the
    filter merges ``noopener`` and ``noreferrer`` into its ``rel``
    attribute. Existing editor tokens (e.g. ``nofollow``, ``ugc``) are
    preserved and the merged set is deduplicated while keeping the
    editor's ordering stable. All other anchors (mailto, relative,
    fragment, ``javascript:``, ``data:``, etc.) are left untouched so
    this filter never silently whitelists unsafe schemes — Wagtail's
    upstream sanitiser strips those before rendering reaches us.

    The filter is intended for per-banner use only. It must never be
    applied globally, since that would rewrite anchors inside unrelated
    content such as the ``AlertBlock`` StreamField.

    Args:
        value (str): Rendered rich-text HTML (typically the snippet's
            ``message`` field after Wagtail's default ``|richtext``
            pipeline).

    Returns:
        SafeString: The mutated HTML, marked safe for template
            inclusion.
    """
    soup = BeautifulSoup(value, "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if not href.startswith(_EXTERNAL_HREF_PREFIXES):
            continue
        existing = anchor.get("rel") or []
        if isinstance(existing, str):
            existing = existing.split()
        merged: list[str] = []
        seen: set[str] = set()
        for token in (*existing, *_REQUIRED_REL_TOKENS):
            if token and token not in seen:
                merged.append(token)
                seen.add(token)
        anchor["rel"] = merged
    return mark_safe(str(soup))
