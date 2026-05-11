"""Tests for the external link handler."""

from django.test import SimpleTestCase
from wagtail.rich_text import features

from cms.handlers.external_link import ExternalLinkNewTabHandler


class TestExternalLinkNewTabHandler(SimpleTestCase):
    """Tests for the ExternalLinkNewTabHandler."""

    def test_identifier(self):
        """Test that the identifier is set correctly."""
        self.assertEqual(ExternalLinkNewTabHandler.identifier, "external")

    def test_expand_db_attributes(self):
        """Test that the expand_db_attributes method returns the correct HTML."""
        attrs = {"href": "https://example.com"}
        expected_html = "<a href='https://example.com' target='_blank' rel='noopener noreferrer'>"
        self.assertEqual(ExternalLinkNewTabHandler.expand_db_attributes(attrs), expected_html)

    def test_expand_db_attributes_escapes_href(self):
        """Test that the expand_db_attributes method escapes the href attribute."""
        attrs = {"href": "'><script>alert('xss')</script>"}

        result = ExternalLinkNewTabHandler.expand_db_attributes(attrs)

        self.assertIn("&lt;script&gt;", result)
        self.assertNotIn("<script>", result)

    def test_expand_db_attributes_requires_href(self):
        """Test that the expand_db_attributes method raises a KeyError if href is missing."""
        with self.assertRaises(KeyError):
            ExternalLinkNewTabHandler.expand_db_attributes({})


class TestExternalLinkFeature(SimpleTestCase):
    """Tests for the external link feature registration."""

    def test_register_external_link(self):
        """Test that the external link handler is registered as a rich text feature."""
        features_link_types = features.get_link_types()

        self.assertIn("external", features_link_types)
        self.assertIs(features_link_types["external"], ExternalLinkNewTabHandler)
