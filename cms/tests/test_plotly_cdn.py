"""Tests for Plotly.js CDN helpers."""

from django.template import Context, Template
from django.test import SimpleTestCase

from dashboard_viz.utils.plotly import get_plotlyjs_cdn_param


class TestPlotlyCdn(SimpleTestCase):
    """Tests for get_plotlyjs_cdn_param."""

    def test_returns_cdn_url(self) -> None:
        """Test that the CDN URL is extracted from Plotly's HTML output."""
        url = get_plotlyjs_cdn_param("url")
        self.assertIsNotNone(url)
        self.assertIn("cdn.plot.ly", url or "")
        self.assertTrue((url or "").endswith(".js"))

    def test_returns_integrity_hash(self) -> None:
        """Test that the SRI hash is extracted from Plotly's HTML output."""
        integrity = get_plotlyjs_cdn_param("hash")
        self.assertIsNotNone(integrity)
        self.assertTrue((integrity or "").startswith("sha256-"))

    def test_invalid_param_returns_none(self) -> None:
        """Test that unknown parameter names return None."""
        self.assertIsNone(get_plotlyjs_cdn_param("invalid"))


class TestPlotlyJsTemplateTag(SimpleTestCase):
    """Tests for the plotlyjs_once template tag."""

    def test_plotlyjs_once_includes_script_only_once(self) -> None:
        """Test that plotlyjs_once emits one script tag per render context."""
        template = Template("{% load plotly_js %}{% plotlyjs_once %}{% plotlyjs_once %}")
        rendered = template.render(Context())
        self.assertEqual(rendered.count("<script"), 1)
        self.assertIn("cdn.plot.ly", rendered)
