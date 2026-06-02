"""Custom template filters for the portal_data app."""

from django import template

register = template.Library()


@register.filter
def facet_label(value: str) -> str:
    """Convert a field name like 'design_types' to a readable label 'Design Types'."""
    return str(value).replace("_", " ").title()
