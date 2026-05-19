"""External link handler in Rich Text."""

from html import escape

from wagtail.rich_text import LinkHandler


class ExternalLinkNewTabHandler(LinkHandler):
    """Custom link handler for external links that opens in a new tab."""

    identifier = "external"

    @classmethod
    def expand_db_attributes(cls, attrs: dict[str, str]) -> str:
        """Expand the database attributes to an HTML anchor tag."""
        attrs["href"] = escape(attrs["href"], quote=True)
        attrs["target"] = "_blank"

        existing_rel = escape(attrs.get("rel", ""), quote=True)
        for required_rel in ["noopener", "noreferrer"]:
            if required_rel not in existing_rel:
                existing_rel = f"{existing_rel} {required_rel}".strip()
        attrs["rel"] = existing_rel

        # Flatten the attributes into a string for the anchor tag
        flattened = " ".join(f'{key}="{value}"' for key, value in sorted(attrs.items()))

        return f"<a {flattened}>"
