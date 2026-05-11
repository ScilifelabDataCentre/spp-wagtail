"""External link handler in Rich Text."""

from django.utils.html import escape
from wagtail.rich_text import LinkHandler


class ExternalLinkNewTabHandler(LinkHandler):
    """Custom link handler for external links that opens in a new tab."""

    identifier = "external"

    @classmethod
    def expand_db_attributes(cls, attrs: dict[str, str]) -> str:
        """Expand the database attributes to an HTML anchor tag."""
        href = escape(attrs["href"])
        return f"<a href='{href}' target='_blank' rel='noopener noreferrer'>"
