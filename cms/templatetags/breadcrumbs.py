"""Template tags for generating breadcrumb navigation."""

import structlog
from django import template
from wagtail.models import Page

register = template.Library()

LOGGER = structlog.get_logger(__name__)


def get_breadcrumbs(page: Page) -> list[dict[str, str]]:
    """Generate a list of breadcrumbs for the given page."""

    try:
        # ancestors includes root usually, so we filter out those with depth <= 1
        ancestors = page.get_ancestors(inclusive=True).filter(depth__gt=1).live().public()

        crumbs = []
        for ancestor in ancestors:
            crumbs.append({"title": ancestor.title, "url": ancestor.url})

        return crumbs
    except Page.DoesNotExist:
        LOGGER.warning("Page does not exist for breadcrumbs", page_id=page.id)
    except AttributeError:
        LOGGER.warning("Page object missing attributes for breadcrumbs", page_id=page.id)
    except Exception as e:
        LOGGER.error("Error generating breadcrumbs", error=str(e), page_id=page.id)

    return []


@register.inclusion_tag("cms/components/breadcrumbs.html", takes_context=True)
def breadcrumbs_display(context: template.Context) -> dict[str, list[dict[str, str]]]:
    """Render the breadcrumbs HTML for the current page."""
    page = context.get("page")

    # skip if no page or if it's the homepage or root
    if page is None or page.depth <= 2:
        return {}

    return {"breadcrumbs_list": get_breadcrumbs(page)}
