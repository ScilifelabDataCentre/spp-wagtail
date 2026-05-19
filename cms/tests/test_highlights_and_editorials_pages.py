"""Tests for highlights and editorials pages."""

from unittest.mock import MagicMock, patch

from django.http import Http404, HttpResponse, QueryDict
from django.test import RequestFactory, SimpleTestCase
from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase

from cms.pages import (
    HighlightsAndEditorialsIndexPage,
    HighlightsAndEditorialsPage,
    HomePage,
)
from cms.services.highlights_and_editorials import (
    SEARCH_MAX_LENGTH,
    get_related_articles,
    validate_filters,
)
from cms.tests.utils import create_test_image

#######################################################################
############# Helper classes and functions for testing ################
#######################################################################


class BasePageTestCase(WagtailPageTestCase):
    """Base test case for page tests, providing common setup and utilities."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Create a site setup with a home page and a highlights/editorials index page."""

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

        cls.index_page = HighlightsAndEditorialsIndexPage(
            title="Highlights and Editorials", slug="highlights-and-editorials"
        )
        cls.home.add_child(instance=cls.index_page)
        cls.index_page.save_revision().publish()


#######################################################################################
############### Test suite for HighlightsAndEditorialsIndexPage model #################
#######################################################################################


class TestHighlightsAndEditorialsIndexPage(BasePageTestCase):
    """Tests for the HighlightsAndEditorialsIndexPage model."""

    def test_max_count_set_on_model(self):
        """Test that only one instance of HighlightsAndEditorialsIndexPage can be created."""
        self.assertEqual(HighlightsAndEditorialsIndexPage.max_count, 1)

    def test_parent_page_type_restriction(self):
        """Test that only HomePage can be a parent of HighlightsAndEditorialsIndexPage."""
        self.assertEqual(HighlightsAndEditorialsIndexPage.parent_page_types, ["cms.HomePage"])

    def test_subpage_type_restriction(self):
        """Test that only HighlightsAndEditorialsPage can be added as a child."""
        self.assertEqual(
            HighlightsAndEditorialsIndexPage.subpage_types, ["cms.HighlightsAndEditorialsPage"]
        )

    @patch("cms.pages.highlights_and_editorials.validate_filters")
    def test_get_context_adds_filter_metadata(self, mock_validate_filters: MagicMock):
        """Test that get_context adds the correct filter metadata to the context."""
        mock_validate_filters.return_value = {}

        request = self.factory.get("/")

        with (
            patch("cms.pages.HighlightsAndEditorialsTopic.objects.filter") as mock_topic_filter,
            patch("cms.pages.HighlightsAndEditorialsPage.objects.child_of") as mock_child_of,
        ):
            # Mock topics queryset chain
            mock_topic_filter.return_value.values_list.return_value.distinct.return_value = [
                "COVID-19",
                "Infectious Diseases",
            ]

            # Mock article queryset chain
            mock_queryset = MagicMock()
            (
                mock_child_of.return_value.live.return_value.prefetch_related.return_value.order_by.return_value.distinct.return_value.filter.return_value
            ) = mock_queryset

            context = self.index_page.get_context(request)

        self.assertEqual(context["all_topics"], ["COVID-19", "Infectious Diseases"])
        self.assertEqual(
            context["all_article_types"],
            ["Data Highlight", "Editorial"],
        )
        self.assertEqual(context["articles_list"], mock_queryset)

        mock_validate_filters.assert_called_once_with(
            request.GET,
            valid_topics=["COVID-19", "Infectious Diseases"],
            valid_types=["Data Highlight", "Editorial"],
        )

    @patch("cms.pages.highlights_and_editorials.validate_filters")
    def test_get_context_applies_search_filter(self, mock_validate_filters: MagicMock):
        """Test that get_context applies the search filter correctly."""
        mock_validate_filters.return_value = {
            "search": "influenza",
        }

        request = self.factory.get("/?search=influenza")

        with (
            patch("cms.pages.HighlightsAndEditorialsTopic.objects.filter") as mock_topic_filter,
            patch("cms.pages.HighlightsAndEditorialsPage.objects.child_of") as mock_child_of,
        ):
            mock_topic_filter.return_value.values_list.return_value.distinct.return_value = []

            mock_filter = MagicMock()

            queryset_chain = mock_child_of.return_value.live.return_value.prefetch_related.return_value.order_by.return_value.distinct.return_value  # noqa: E501

            queryset_chain.filter.return_value = mock_filter

            context = self.index_page.get_context(request)

        self.assertEqual(context["articles_list"], mock_filter)
        queryset_chain.filter.assert_called_once()

    @patch("cms.pages.highlights_and_editorials.render")
    def test_serve_htmx_request_returns_partial_response(self, mock_render: MagicMock):
        """Test the partial response with the correct template and context for HTMX requests."""
        request = self.factory.get("/?search=test&type=Editorial")
        request.htmx = True

        mock_response = HttpResponse("partial")
        mock_render.return_value = mock_response

        with patch.object(self.index_page, "get_context", return_value={"articles_list": []}):
            response = self.index_page.serve(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["HX-Replace-Url"], "/?type=Editorial")

        mock_render.assert_called_once_with(
            request,
            "cms/components/highlights_and_editorials_list.html#articles_grid",
            {"articles_list": []},
        )

    @patch("cms.pages.HighlightsAndEditorialsIndexPage.serve")
    def test_serve_non_htmx_delegates_to_super(self, mock_super_serve: MagicMock):
        """Test that non-HTMX requests are handled by the superclass serve method."""
        request = self.factory.get("/")
        request.htmx = False

        mock_super_serve.return_value = HttpResponse("full page")

        response = self.index_page.serve(request)

        self.assertEqual(response.content, b"full page")
        mock_super_serve.assert_called_once_with(request)


##################################################################################
############### Test suite for HighlightsAndEditorialsPage model #################
##################################################################################


class TestHighlightsAndEditorialsPage(BasePageTestCase):
    """Tests for the HighlightsAndEditorialsPage model."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Create a HighlightsAndEditorialsPage instance for testing."""

        super().setUpTestData()

        image = create_test_image(title="Test Image", file_name="test_image.jpg")
        cls.editorial_page = HighlightsAndEditorialsPage(
            title="Article",
            slug="article",
            image=image,
            description="Test description",
            article_type="editorial",
            keywords="COVID-19, Infectious Diseases",
        )

        cls.index_page.add_child(instance=cls.editorial_page)
        cls.editorial_page.save_revision().publish()

    def test_parent_page_type_restriction(self):
        """Test that only HighlightsAndEditorialsIndexPage can be the parent."""
        self.assertEqual(
            HighlightsAndEditorialsPage.parent_page_types, ["cms.HighlightsAndEditorialsIndexPage"]
        )

    def test_subpage_type_restriction(self):
        """Test that no child pages can be added to HighlightsAndEditorialsPage."""
        self.assertEqual(HighlightsAndEditorialsPage.subpage_types, [])

    def test_image_field_is_required_by_model_constraint(self):
        """Test that the image field is required based on the model definition."""
        field = HighlightsAndEditorialsPage._meta.get_field("image")
        self.assertFalse(field.blank)

    def test_description_is_required_by_model_constraint(self):
        """Test that the description field is required based on the model definition."""
        field = HighlightsAndEditorialsPage._meta.get_field("description")
        self.assertFalse(field.blank)

    def test_status_field_is_required_by_model_constraint(self):
        """Test that the status field is required based on the model definition."""
        field = HighlightsAndEditorialsPage._meta.get_field("article_type")
        self.assertFalse(field.blank)

    def test_status_field_has_correct_choices(self):
        """Test that the status field has the correct choices defined."""
        field = HighlightsAndEditorialsPage._meta.get_field("article_type")
        expected_choices = [("data-highlight", "Data Highlight"), ("editorial", "Editorial")]
        self.assertEqual(field.choices, expected_choices)

    def test_keyword_list_returns_cleaned_keywords(self):
        """Test that the keyword_list property returns a cleaned list of keywords."""
        self.assertEqual(self.editorial_page.keyword_list, ["covid-19", "infectious diseases"])

    def test_topics_returns_topics_sorted_by_title(self):
        """Test that the topics property returns topics sorted alphabetically by title."""
        topic_b = MagicMock()
        topic_b.title = "Zebra"

        topic_a = MagicMock()
        topic_a.title = "AI"

        rel1 = MagicMock(topic=topic_b)
        rel2 = MagicMock(topic=topic_a)

        manager_cls = self.editorial_page.article_topics.__class__

        with patch.object(manager_cls, "all", return_value=[rel1, rel2]):
            topics = list(self.editorial_page.topics)

        self.assertEqual([topic.title for topic in topics], ["AI", "Zebra"])

    @patch("cms.pages.highlights_and_editorials.get_related_articles")
    def test_get_context_adds_parent_heading_and_related_articles(
        self, mock_related_articles: MagicMock
    ):
        """Test that the parent page heading and related articles are added to the context."""
        request = self.factory.get("/")

        related_articles = [MagicMock(), MagicMock()]
        mock_related_articles.return_value = related_articles

        context = self.editorial_page.get_context(request)

        # The page heading should be same as the parent index page title set in setUpTestData
        self.assertEqual(context["page_heading"], "Highlights and Editorials")
        self.assertEqual(context["related_articles"], related_articles)

        mock_related_articles.assert_called_once_with(self.editorial_page)


######################################################################################
############### Test suite for get_related_articles service function #################
######################################################################################


class TestGetRelatedArticles(SimpleTestCase):
    """Tests for the get_related_articles service function."""

    def create_mock_article(
        self,
        *,
        article_id: int,
        keywords: str,
        article_type: str = "editorial",
        title: str = "Article",
    ) -> MagicMock:
        """Create a mock article with specified attributes."""
        article = MagicMock()
        article.id = article_id
        article.title = title
        article.article_type = article_type
        article.keywords = keywords
        article.keyword_list = [
            keyword.strip().lower() for keyword in keywords.split(",") if keyword.strip()
        ]

        return article

    def test_returns_empty_queryset_when_article_has_no_keywords(self) -> None:
        """Test that an empty queryset is returned when the article has no keywords."""
        article_model = MagicMock()

        article = MagicMock()
        article.specific.__class__ = article_model
        article.keyword_list = []

        empty_queryset = MagicMock()
        article_model.objects.none.return_value = empty_queryset

        result = get_related_articles(article)

        self.assertEqual(result, empty_queryset)
        article_model.objects.none.assert_called_once()

    def test_returns_empty_queryset_when_no_candidate_articles_exist(self) -> None:
        """Test that an empty queryset is returned when there are no candidate articles."""
        article_model = MagicMock()

        article = self.create_mock_article(
            article_id=1,
            keywords="covid-19, infectious diseases",
        )
        article.specific.__class__ = article_model

        queryset = MagicMock()
        queryset.exists.return_value = False

        (
            article_model.objects.live.return_value.filter.return_value.exclude.return_value.order_by.return_value
        ) = queryset

        empty_queryset = MagicMock()
        article_model.objects.none.return_value = empty_queryset

        result = get_related_articles(article)

        self.assertEqual(result, empty_queryset)
        queryset.exists.assert_called_once()

    def test_returns_related_articles_sorted_by_similarity(self) -> None:
        """Test that related articles are returned sorted by similarity score."""
        article_model = MagicMock()

        main_article = self.create_mock_article(
            article_id=1, keywords="covid-19, infectious diseases, vaccines"
        )
        main_article.specific.__class__ = article_model

        related_high = self.create_mock_article(
            article_id=2, keywords="covid-19, infectious diseases", title="High Similarity"
        )

        related_low = self.create_mock_article(
            article_id=3, keywords="covid-19", title="Low Similarity"
        )

        unrelated = self.create_mock_article(
            article_id=4, keywords="antibiotics", title="Unrelated"
        )

        queryset = MagicMock()
        queryset.exists.return_value = True
        queryset.iterator.return_value = [related_low, unrelated, related_high]

        (
            article_model.objects.live.return_value.filter.return_value.exclude.return_value.order_by.return_value
        ) = queryset

        result = get_related_articles(main_article, limit=2, threshold=0.1)

        self.assertEqual(result, [related_high, related_low])

    def test_excludes_articles_below_threshold(self) -> None:
        """Test that articles with similarity below the threshold are excluded."""
        article_model = MagicMock()

        main_article = self.create_mock_article(
            article_id=1, keywords="covid-19, infectious diseases, vaccines"
        )
        main_article.specific.__class__ = article_model

        weak_match = self.create_mock_article(article_id=2, keywords="covid-19, antibiotics")

        queryset = MagicMock()
        queryset.exists.return_value = True
        queryset.iterator.return_value = [weak_match]

        (
            article_model.objects.live.return_value.filter.return_value.exclude.return_value.order_by.return_value
        ) = queryset

        result = get_related_articles(main_article, threshold=0.9)

        self.assertEqual(result, [])

    def test_skips_articles_without_keywords(self) -> None:
        """Test that articles without keywords are skipped in similarity calculations."""
        article_model = MagicMock()

        main_article = self.create_mock_article(
            article_id=1, keywords="covid-19, infectious diseases"
        )
        main_article.specific.__class__ = article_model

        no_keywords_article = MagicMock()
        no_keywords_article.keywords = ""
        no_keywords_article.keyword_list = []

        queryset = MagicMock()
        queryset.exists.return_value = True
        queryset.iterator.return_value = [no_keywords_article]

        (
            article_model.objects.live.return_value.filter.return_value.exclude.return_value.order_by.return_value
        ) = queryset

        result = get_related_articles(main_article)

        self.assertEqual(result, [])

    def test_limits_number_of_results(self) -> None:
        """Test that the number of related articles returned does not exceed the specified limit."""
        article_model = MagicMock()

        main_article = self.create_mock_article(
            article_id=1,
            keywords="covid-19, infectious diseases, vaccines",
        )
        main_article.specific.__class__ = article_model

        article_1 = self.create_mock_article(
            article_id=2, keywords="covid-19, antibiotics, vaccines", title="A1"
        )

        article_2 = self.create_mock_article(
            article_id=3, keywords="covid-19, bacteria, vaccines", title="A2"
        )

        article_3 = self.create_mock_article(article_id=4, keywords="covid-19", title="A3")

        queryset = MagicMock()
        queryset.exists.return_value = True
        queryset.iterator.return_value = [article_1, article_2, article_3]

        (
            article_model.objects.live.return_value.filter.return_value.exclude.return_value.order_by.return_value
        ) = queryset

        result = get_related_articles(main_article, limit=2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result, [article_1, article_2])


##################################################################################
############### Test suite for validate_filters service function #################
##################################################################################


class TestValidateFilters(SimpleTestCase):
    """Tests for the validate filters utility function."""

    def setUp(self) -> None:
        """Set up test data for filter validation tests."""
        self.valid_topics = ["COVID-19", "Infectious Diseases"]
        self.valid_types = ["data-highlight", "editorial"]

    def test_valid_filters_returned_as_expected(self):
        """Test that valid filters are returned correctly."""
        request = MagicMock()
        request.GET = QueryDict("search=test&type=editorial&topic=covid-19")

        filters = validate_filters(request.GET, self.valid_topics, self.valid_types)

        self.assertEqual(filters["search"], "test")
        self.assertIn("editorial", filters["type"])
        self.assertIn("covid-19", filters["topic"])

    def test_invalid_type_filter_raises_http404(self):
        """Test that an invalid type filter raises an Http404 error."""
        request = MagicMock()
        request.GET = QueryDict("type=invalid")

        with self.assertRaises(Http404):
            validate_filters(request.GET, self.valid_topics, self.valid_types)

    def test_raises_404_for_too_many_article_types(self) -> None:
        """Test that selecting too many article types raises an Http404 error."""
        querydict = QueryDict("type=editorial&type=data-highlight&type=extra")

        with self.assertRaises(Http404):
            validate_filters(querydict, valid_types=self.valid_types)

    def test_invalid_topic_filter_raises_http404(self):
        """Test that an invalid topic filter raises an Http404 error."""
        request = MagicMock()
        request.GET = QueryDict("topic=InvalidTopic")

        with self.assertRaises(Http404):
            validate_filters(request.GET, self.valid_topics, self.valid_types)

    def test_raises_404_for_too_many_topics(self) -> None:
        """Test that selecting too many topics raises an Http404 error."""
        querydict = QueryDict("topic=covid-19&topic=infectious-diseases&topic=extra")

        with self.assertRaises(Http404):
            validate_filters(querydict, valid_topics=self.valid_topics)

    def test_raises_404_for_search_query_too_long(self) -> None:
        """Test that a search query exceeding the maximum length raises an Http404 error."""
        querydict = QueryDict(f"search={'a' * (SEARCH_MAX_LENGTH + 1)}")

        with self.assertRaises(Http404):
            validate_filters(querydict)

    def test_returns_default_filters_for_empty_querydict(self) -> None:
        """Test that default filters are returned when an empty QueryDict is provided."""
        querydict = QueryDict("")

        result = validate_filters(querydict)

        self.assertEqual(result, {"search": "", "topic": [], "type": []})
