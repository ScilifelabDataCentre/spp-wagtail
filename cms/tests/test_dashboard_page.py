"""Tests for DashboardPage and DashboardIndexPage."""

from django.core.files.uploadedfile import SimpleUploadedFile
from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase

from cms.pages.dashboard import DATA_STATUS_CHOICES, DashboardPage
from cms.pages.dashboard_index import DashboardIndexPage
from cms.pages.home import HomePage
from cms.snippets.dashboard_data import DashboardData
from cms.tests.utils import create_test_image


class DashboardPageTestCase(WagtailPageTestCase):
    """Base test case that creates the page tree for dashboard tests."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Create site with home page and dashboard index page."""
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

        cls.index = DashboardIndexPage(title="Dashboards", slug="dashboards")
        cls.home.add_child(instance=cls.index)
        cls.index.save_revision().publish()


class TestDashboardPageModel(DashboardPageTestCase):
    """Tests for the DashboardPage model fields and constraints."""

    def test_parent_page_type_restriction(self) -> None:
        """Test that only DashboardIndexPage can be a parent."""
        self.assertEqual(DashboardPage.parent_page_types, ["cms.DashboardIndexPage"])

    def test_subpage_type_restriction(self) -> None:
        """Test that DashboardPage cannot have child pages."""
        self.assertEqual(DashboardPage.subpage_types, [])

    def test_data_status_has_correct_choices(self) -> None:
        """Test that data_status field has active and historic choices."""
        field = DashboardPage._meta.get_field("data_status")
        self.assertEqual(field.choices, DATA_STATUS_CHOICES)

    def test_data_status_has_no_default(self) -> None:
        """Test that data_status has no default (editor must select)."""
        field = DashboardPage._meta.get_field("data_status")
        self.assertFalse(field.has_default())


class TestDashboardPageContext(DashboardPageTestCase):
    """Tests for DashboardPage.get_context method."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Create a dashboard page for context tests."""
        super().setUpTestData()
        cls.image = create_test_image(title="Dash Image", file_name="dash.jpg")
        cls.page = DashboardPage(
            title="Serology",
            slug="serology-statistics",
            description="Serology test dashboard",
            image=cls.image,
            data_status="active",
        )
        cls.index.add_child(instance=cls.page)
        cls.page.save_revision().publish()

    def test_get_context_includes_figures_from_dashboard_data(self) -> None:
        """Test that get_context provides figures from DashboardData."""
        csv_file = SimpleUploadedFile("data.csv", b"a,b\n1,2\n", "text/csv")
        data_row = DashboardData.objects.create(
            dashboard_slug="serology-statistics",
            source_file=csv_file,
        )
        data_row.data = {"chart_1": {"data": [], "layout": {}}}
        data_row.save(update_fields=["data"])

        request = self.client.get(self.page.url).wsgi_request
        context = self.page.get_context(request)

        self.assertIn("figures", context)
        self.assertIn("chart_1", context["figures"])

    def test_get_context_handles_missing_dashboard_data(self) -> None:
        """Test that get_context works when no DashboardData exists."""
        request = self.client.get(self.page.url).wsgi_request
        context = self.page.get_context(request)

        self.assertEqual(context["figures"], {})
        self.assertIsNone(context["dashboard_data"])

    def test_get_context_includes_dashboard_data_object(self) -> None:
        """Test that the full DashboardData object is in context."""
        csv_file = SimpleUploadedFile("data2.csv", b"x,y\n3,4\n", "text/csv")
        data_row = DashboardData.objects.create(
            dashboard_slug="serology-statistics",
            source_file=csv_file,
        )
        data_row.data = {"fig_a": {"data": [1], "layout": {}}}
        data_row.save(update_fields=["data"])

        request = self.client.get(self.page.url).wsgi_request
        context = self.page.get_context(request)

        self.assertEqual(context["dashboard_data"].pk, data_row.pk)

    def test_get_context_includes_data_updated_at(self) -> None:
        """Test that get_context exposes the public data freshness date."""
        from datetime import date

        source_file = SimpleUploadedFile("data3.csv", b"x,y\n3,4\n", "text/csv")
        data_row = DashboardData.objects.create(
            dashboard_slug="serology-statistics",
            source_file=source_file,
            data={},
        )
        data_row.data_updated_at = date(2024, 3, 1)
        data_row.save(update_fields=["data_updated_at"])

        request = self.client.get(self.page.url).wsgi_request
        context = self.page.get_context(request)

        self.assertEqual(context["data_updated_at"], date(2024, 3, 1))


class TestDashboardIndexPageModel(DashboardPageTestCase):
    """Tests for the DashboardIndexPage model."""

    def test_max_count_is_one(self) -> None:
        """Test that only one DashboardIndexPage can exist."""
        self.assertEqual(DashboardIndexPage.max_count, 1)

    def test_parent_page_type_restriction(self) -> None:
        """Test that only HomePage can be a parent."""
        self.assertEqual(DashboardIndexPage.parent_page_types, ["cms.HomePage"])

    def test_subpage_types_allows_dashboard_page(self) -> None:
        """Test that DashboardPage is the only allowed child."""
        self.assertEqual(DashboardIndexPage.subpage_types, ["cms.DashboardPage"])

    def test_get_context_groups_dashboards_by_status(self) -> None:
        """Test that get_context groups child dashboards by data_status."""
        image = create_test_image(title="Idx Image", file_name="idx.jpg")
        updating_page = DashboardPage(
            title="Active Dashboard",
            slug="active-dash",
            description="Active",
            image=image,
            data_status="active",
        )
        self.index.add_child(instance=updating_page)
        updating_page.save_revision().publish()

        image2 = create_test_image(title="Idx Image2", file_name="idx2.jpg")
        historic_page = DashboardPage(
            title="Old Dashboard",
            slug="old-dash",
            description="Historic",
            image=image2,
            data_status="historic",
        )
        self.index.add_child(instance=historic_page)
        historic_page.save_revision().publish()

        request = self.client.get(self.index.url).wsgi_request
        context = self.index.get_context(request)

        self.assertIn("active", context["dashboards"])
        self.assertIn("historic", context["dashboards"])
