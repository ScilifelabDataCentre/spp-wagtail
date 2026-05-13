"""Tests for the CataloguePage model."""

from unittest.mock import MagicMock, patch

from django.http import Http404, HttpResponse, QueryDict
from django.test import RequestFactory, SimpleTestCase
from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase

from cms.pages import CataloguePage, HomePage
from cms.services.catalogue import SEARCH_MAX_LENGTH, validate_filters
from cms.tests.utils import create_test_image


class TestCataloguePage(WagtailPageTestCase):
    """Base test case for page tests, providing common setup and utilities."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Create a site setup with a home page and a catalogue page."""

        cls.factory = RequestFactory()
        root = Page.get_first_root_node()
        for child in root.get_children():
            child.delete()
        root = Page.get_first_root_node()
        cls.home = HomePage(title="Home", slug="home")
        root.add_child(instance=cls.home)
        Site.objects.update_or_create(
            is_default_site=True,
            defaults={"hostname": "testserver", "root_page": cls.home},
        )

        image1 = create_test_image(title="Image 1", file_name="test_image1.jpg")
        image2 = create_test_image(title="Image 2", file_name="test_image2.jpg")
        cls.catalogue = CataloguePage(
            title="Catalogue",
            slug="catalogue",
            filter_label="Catalogue Type",
            content=[
                (
                    "card_grid",
                    {
                        "cards": [
                            {
                                "title": "Bravo",
                                "description": "Bravo description",
                                "image": image1,
                                "url": "/bravo/",
                                "type": "Guides, Tools",
                                "keywords": "beta second",
                            },
                            {
                                "title": "Alpha",
                                "description": "Alpha description",
                                "image": image2,
                                "url": "/alpha/",
                                "type": "Tools",
                                "keywords": "first",
                            },
                        ]
                    },
                )
            ],
        )
        cls.home.add_child(instance=cls.catalogue)
        cls.catalogue.save_revision().publish()

    def test_parent_page_type_restriction(self):
        """Test that only HomePage can be a parent of CataloguePage."""
        self.assertEqual(CataloguePage.parent_page_types, ["cms.HomePage"])

    def test_subpage_type_restriction(self):
        """Test that only CataloguePage can be added as a child."""
        self.assertEqual(CataloguePage.subpage_types, [])

    def test_cards_returns_sorted_cards(self):
        """Test that the cards property returns cards sorted by title."""
        cards = self.catalogue.cards

        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0]["title"], "Alpha")
        self.assertEqual(cards[1]["title"], "Bravo")

    def test_card_types_returns_unique_sorted_types(self):
        """Test that the card_types property returns unique, sorted types."""
        self.assertEqual(self.catalogue.card_types, ["Guides", "Tools"])

    @patch("cms.pages.catalogue.validate_filters")
    def test_get_context_without_filters(self, mock_validate_filters: MagicMock):
        """Test get_context returns all cards when no filters are applied."""
        mock_validate_filters.return_value = {}

        request = self.factory.get("/catalogue/")
        context = self.catalogue.get_context(request)

        self.assertEqual(context["catalogue_types"], ["Guides", "Tools"])
        self.assertEqual(len(context["catalogue_list"]), 2)

    @patch("cms.pages.catalogue.validate_filters")
    def test_get_context_filters_by_search(self, mock_validate_filters: MagicMock):
        """Test get_context filters cards based on search query."""
        mock_validate_filters.return_value = {
            "search": "alpha",
        }

        request = self.factory.get("/catalogue/?search=alpha")
        context = self.catalogue.get_context(request)

        self.assertEqual(len(context["catalogue_list"]), 1)
        self.assertEqual(context["catalogue_list"][0]["title"], "Alpha")

    @patch("cms.pages.catalogue.validate_filters")
    def test_get_context_filters_by_type(self, mock_validate_filters: MagicMock):
        """Test get_context filters cards based on type filter."""
        mock_validate_filters.return_value = {"type": ["guides"]}

        request = self.factory.get("/catalogue/?type=guides")
        context = self.catalogue.get_context(request)

        self.assertEqual(len(context["catalogue_list"]), 1)
        self.assertEqual(context["catalogue_list"][0]["title"], "Bravo")
        self.assertEqual(context["type_filter"], ["guides"])

    @patch("cms.pages.catalogue.render")
    def test_serve_htmx_request(self, mock_render: MagicMock):
        """Test that serve returns filtered content for HTMX requests."""
        mock_response = HttpResponse("filtered content")
        mock_render.return_value = mock_response

        request = self.factory.get("/catalogue/?search=test&type=guides")
        request.htmx = True

        response = self.catalogue.serve(request)

        mock_render.assert_called_once()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["HX-Replace-Url"], "/catalogue/?type=guides")

    @patch("cms.pages.catalogue.CataloguePage.serve")
    def test_serve_non_htmx_request(self, mock_super_serve: MagicMock):
        """Test that serve returns normal response for non-HTMX requests."""
        mock_super_serve.return_value = HttpResponse("normal response")

        request = self.factory.get("/catalogue/")
        request.htmx = False

        response = self.catalogue.serve(request)

        mock_super_serve.assert_called_once_with(request)
        self.assertEqual(response.content, b"normal response")


##################################################################################
############### Test suite for validate_filters service function #################
##################################################################################


class TestValidateFilters(SimpleTestCase):
    """Tests for the validate filters utility function."""

    def setUp(self) -> None:
        """Set up test data for filter validation tests."""
        self.valid_types = ["guides", "tools"]

    def test_valid_filters_returned_as_expected(self):
        """Test that valid filters are returned correctly."""
        request = MagicMock()
        request.GET = QueryDict("search=test&type=guides")

        filters = validate_filters(request.GET, self.valid_types)

        self.assertEqual(filters["search"], "test")
        self.assertIn("guides", filters["type"])

    def test_invalid_type_filter_raises_http404(self):
        """Test that an invalid type filter raises an Http404 error."""
        request = MagicMock()
        request.GET = QueryDict("type=invalid")

        with self.assertRaises(Http404):
            validate_filters(request.GET, self.valid_types)

    def test_raises_404_for_too_many_article_types(self) -> None:
        """Test that selecting too many article types raises an Http404 error."""
        querydict = QueryDict("type=guides&type=tools&type=extra")

        with self.assertRaises(Http404):
            validate_filters(querydict, valid_types=self.valid_types)

    def test_raises_404_for_search_query_too_long(self) -> None:
        """Test that a search query exceeding the maximum length raises an Http404 error."""
        querydict = QueryDict(f"search={'a' * (SEARCH_MAX_LENGTH + 1)}")

        with self.assertRaises(Http404):
            validate_filters(querydict)

    def test_returns_default_filters_for_empty_querydict(self) -> None:
        """Test that default filters are returned when an empty QueryDict is provided."""
        querydict = QueryDict("")

        result = validate_filters(querydict)

        self.assertEqual(result, {"search": "", "type": []})
