"""Template tags for generating breadcrumb navigation."""

import structlog
from django import template
from wagtail.models import Page

register = template.Library()

LOGGER = structlog.get_logger(__name__)


def get_ancestors(page: Page) -> list[dict[str, str | None]]:
    """Generate a list of ancestors (excluding root) for the given page."""

    try:
        # ancestors includes root usually, so we filter out those with depth <= 1
        # `.live()` and `.public()` are not needed here since we want to show the
        # breadcrumbs even for non-live and non-public pages for preview purposes.
        ancestors = page.get_ancestors().filter(depth__gt=1)

        crumbs: list[dict[str, str | None]] = []
        for ancestor in ancestors:
            # Only include URLs for live pages; non-live pages should not have
            # clickable links in the breadcrumbs as it would lead to a 404 page.
            crumbs.append({"title": ancestor.title, "url": ancestor.url if ancestor.live else None})

        return crumbs
    except Exception:
        LOGGER.exception(
            "Error generating breadcrumbs",
            page_id=getattr(page, "id", None),
            page_title=getattr(page, "title", None),
        )

    return []


@register.inclusion_tag("cms/components/breadcrumbs.html", takes_context=True)
def breadcrumbs_display(context: template.Context) -> dict[str, list[dict[str, str | None]]]:
    """Render the breadcrumbs HTML for the current page."""
    page = context.get("page")

    # skip if no page or if it's the homepage or root
    if page is None or page.depth <= 2:
        return {}

    return {"ancestors_list": get_ancestors(page), "current_page": page}
