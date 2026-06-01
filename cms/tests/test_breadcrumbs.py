"""Tests for breadcrumb template tags."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.template import Context, Template
from django.test import SimpleTestCase
from wagtail.models import Page

from cms.templatetags.breadcrumbs import breadcrumbs_display, get_ancestors


class TestGetAncestors(SimpleTestCase):
    """Tests for the get_ancestors function."""

    def test_get_ancestors_valid_page(self):
        """Test that get_ancestors returns the correct ancestor list for a valid page."""
        page = MagicMock(spec=Page)
        queryset = MagicMock()
        queryset.filter.return_value = [
            MagicMock(title="Home", url="/"),
            MagicMock(title="Section", url="/section/"),
            # This one should be included but with url=None
            MagicMock(title="Subsection", url="/section/subsection/", live=False),
        ]
        page.get_ancestors.return_value = queryset

        ancestors = get_ancestors(page)
        expected = [
            {"title": "Home", "url": "/"},
            {"title": "Section", "url": "/section/"},
            {"title": "Subsection", "url": None},
        ]

        self.assertEqual(ancestors, expected)
        queryset.filter.assert_called_once_with(depth__gt=1)

    @patch("cms.templatetags.breadcrumbs.LOGGER")
    def test_handles_attribute_error(self, mock_logger: MagicMock):
        """Test that get_ancestors handles AttributeError gracefully."""
        page = MagicMock(id=123)
        page.get_ancestors.side_effect = AttributeError

        ancestors = get_ancestors(page)

        self.assertEqual(ancestors, [])
        mock_logger.warning.assert_called_with(
            "Page object missing attributes for breadcrumbs", page_id=123
        )

    @patch("cms.templatetags.breadcrumbs.LOGGER")
    def test_handles_generic_exception(self, mock_logger: MagicMock):
        """Test that get_ancestors handles generic exceptions gracefully."""
        page = MagicMock(id=456)
        page.get_ancestors.side_effect = RuntimeError("foo")

        result = get_ancestors(page)

        self.assertEqual(result, [])
        mock_logger.exception.assert_called_once_with(
            "Error generating breadcrumbs", error="foo", page_id=456
        )


class TestBreadcrumbsDisplay(SimpleTestCase):
    """Tests for the breadcrumbs_display template tag."""

    def test_breadcrumbs_display_no_page(self):
        """Test that breadcrumbs_display returns an empty context if no page is in context."""
        context = Context({})
        result = breadcrumbs_display(context)

        self.assertEqual(result, {})

    def test_breadcrumbs_display_root_page(self):
        """Test that breadcrumbs_display returns an empty context for root page."""
        context = Context({"page": MagicMock(depth=1)})
        result = breadcrumbs_display(context)

        self.assertEqual(result, {})

    def test_breadcrumbs_display_homepage(self):
        """Test that breadcrumbs_display returns an empty context for homepage page."""
        context = Context({"page": MagicMock(depth=2)})
        result = breadcrumbs_display(context)

        self.assertEqual(result, {})

    @patch("cms.templatetags.breadcrumbs.get_ancestors")
    def test_breadcrumbs_display_valid_page(self, mock_get_ancestors: MagicMock):
        """Test that breadcrumbs_display returns the correct context for a valid page."""
        mock_get_ancestors.return_value = [
            {"title": "Home", "url": "/"},
            {"title": "Section", "url": "/section/"},
        ]

        page = MagicMock(depth=3, title="Current Page")
        context = Context({"page": page})
        result = breadcrumbs_display(context)

        self.assertEqual(
            result, {"ancestors_list": mock_get_ancestors.return_value, "current_page": page}
        )
        mock_get_ancestors.assert_called_once_with(context["page"])

    @patch("cms.templatetags.breadcrumbs.get_ancestors")
    def test_renders_using_breadcrumbs_html_template(self, mock_get_ancestors: MagicMock):
        """Test that breadcrumbs_display renders using the correct template."""
        mock_get_ancestors.return_value = [
            {"title": "Home", "url": "/"},
            {"title": "Section", "url": "/section/"},
        ]

        page = SimpleNamespace(depth=3, title="Current Page")
        rendered = Template("{% load breadcrumbs %}{% breadcrumbs_display %}").render(
            Context({"page": page})
        )

        self.assertIn("Home", rendered)
        self.assertIn('href="/"', rendered)
        self.assertIn("Section", rendered)
        self.assertIn('href="/section/"', rendered)
        # current page title should be present
        self.assertIn("Current Page", rendered)
        mock_get_ancestors.assert_called_once()
