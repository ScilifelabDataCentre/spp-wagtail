"""Tests for breadcrumb template tags."""

from unittest.mock import MagicMock, patch

from django.template import Context, Template
from django.test import SimpleTestCase
from wagtail.models import Page

from cms.templatetags.breadcrumbs import breadcrumbs_display, get_breadcrumbs


class TestGetBreadcrumbs(SimpleTestCase):
    """Tests for the get_breadcrumbs function."""

    def test_get_breadcrumbs_valid_page(self):
        """Test that get_breadcrumbs returns the correct breadcrumb list for a valid page."""
        page = MagicMock(spec=Page)
        queryset = MagicMock()
        queryset.filter.return_value.live.return_value.public.return_value = [
            MagicMock(title="Home", url="/"),
            MagicMock(title="Section", url="/section/"),
            MagicMock(title="Current", url="/section/current/"),
        ]
        page.get_ancestors.return_value = queryset

        breadcrumbs = get_breadcrumbs(page)
        expected = [
            {"title": "Home", "url": "/"},
            {"title": "Section", "url": "/section/"},
            {"title": "Current", "url": "/section/current/"},
        ]

        self.assertEqual(breadcrumbs, expected)
        page.get_ancestors.assert_called_once_with(inclusive=True)
        queryset.filter.assert_called_once_with(depth__gt=1)

    @patch("cms.templatetags.breadcrumbs.LOGGER")
    def test_handles_page_does_not_exist(self, mock_logger: MagicMock):
        """Test that get_breadcrumbs handles Page.DoesNotExist exception gracefully."""
        page = MagicMock(id=123)
        page.get_ancestors.side_effect = Page.DoesNotExist

        breadcrumbs = get_breadcrumbs(page)

        self.assertEqual(breadcrumbs, [])
        mock_logger.warning.assert_called_with("Page does not exist for breadcrumbs", page_id=123)

    @patch("cms.templatetags.breadcrumbs.LOGGER")
    def test_handles_attribute_error(self, mock_logger: MagicMock):
        """Test that get_breadcrumbs handles AttributeError gracefully."""
        page = MagicMock(id=456)
        page.get_ancestors.side_effect = AttributeError

        breadcrumbs = get_breadcrumbs(page)

        self.assertEqual(breadcrumbs, [])
        mock_logger.warning.assert_called_with(
            "Page object missing attributes for breadcrumbs", page_id=456
        )

    @patch("cms.templatetags.breadcrumbs.LOGGER")
    def test_handles_generic_exception(self, mock_logger: MagicMock):
        """Test that get_breadcrumbs handles generic exceptions gracefully."""
        page = MagicMock(id=789)
        page.get_ancestors.side_effect = RuntimeError("foo")

        result = get_breadcrumbs(page)

        self.assertEqual(result, [])
        mock_logger.error.assert_called_once_with(
            "Error generating breadcrumbs", error="foo", page_id=789
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

    @patch("cms.templatetags.breadcrumbs.get_breadcrumbs")
    def test_breadcrumbs_display_valid_page(self, mock_get_breadcrumbs: MagicMock):
        """Test that breadcrumbs_display returns the correct context for a valid page."""
        mock_get_breadcrumbs.return_value = [
            {"title": "Home", "url": "/"},
            {"title": "Section", "url": "/section/"},
        ]

        context = Context({"page": MagicMock(depth=3)})
        result = breadcrumbs_display(context)

        self.assertEqual(result, {"breadcrumbs_list": mock_get_breadcrumbs.return_value})
        mock_get_breadcrumbs.assert_called_once_with(context["page"])

    @patch("cms.templatetags.breadcrumbs.get_breadcrumbs")
    def test_renders_using_breadcrumbs_html_template(self, mock_get_breadcrumbs: MagicMock):
        """Test that breadcrumbs_display renders using the correct template."""
        mock_get_breadcrumbs.return_value = [
            {"title": "Home", "url": "/"},
            {"title": "Section", "url": "/section/"},
        ]

        rendered = Template("{% load breadcrumbs %}{% breadcrumbs_display %}").render(
            Context({"page": MagicMock(depth=3)})
        )

        self.assertIn("Home", rendered)
        self.assertIn('href="/"', rendered)
        self.assertIn("Section", rendered)
        # last breadcrumb should not be a link
        self.assertNotIn('href="/section/"', rendered)
        mock_get_breadcrumbs.assert_called_once()
