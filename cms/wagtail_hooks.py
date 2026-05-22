"""Wagtail hooks for the CMS."""

from wagtail import hooks
from wagtail.rich_text import FeatureRegistry

from .handlers.external_link import ExternalLinkNewTabHandler


@hooks.register("register_rich_text_features")
def register_external_link(features: FeatureRegistry) -> None:
    """Register the external link handler as a rich text feature."""
    features.register_link_type(ExternalLinkNewTabHandler)
