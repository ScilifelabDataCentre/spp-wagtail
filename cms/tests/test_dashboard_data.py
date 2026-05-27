"""Tests for DashboardData model."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from cms.snippets.dashboard_data import DashboardData


class TestDashboardDataModel(TestCase):
    """Tests for the DashboardData model fields and constraints."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Create a DashboardData instance for testing."""
        cls.source_file = SimpleUploadedFile(
            name="test_data.csv",
            content=b"date,value\n2024-01-01,100\n2024-01-02,200\n",
            content_type="text/csv",
        )
        cls.dashboard_data = DashboardData.objects.create(
            dashboard_slug="serology-statistics",
            source_file=cls.source_file,
            data={"serology_chart": {"data": [], "layout": {}}},
            uploaded_by="testuser",
            is_current=True,
        )

    def test_str_representation_includes_slug(self) -> None:
        """Test that string representation includes the dashboard slug."""
        result = str(self.dashboard_data)
        self.assertIn("serology-statistics", result)

    def test_ordering_is_newest_first(self) -> None:
        """Test that default ordering is by uploaded_at descending."""
        self.assertEqual(DashboardData._meta.ordering, ["-uploaded_at"])

    def test_source_file_upload_path(self) -> None:
        """Test that the source file is stored under dashboard_data/."""
        self.assertIn("dashboard_data/", self.dashboard_data.source_file.name)

    def test_data_field_stores_json(self) -> None:
        """Test that the data JSONField stores and retrieves correctly."""
        self.assertEqual(
            self.dashboard_data.data,
            {"serology_chart": {"data": [], "layout": {}}},
        )


class TestDashboardDataGetCurrent(TestCase):
    """Tests for the DashboardData.get_current class method."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Create DashboardData instances with different current states."""
        cls.source_file = SimpleUploadedFile(
            name="current.csv",
            content=b"date,value\n2024-01-01,100\n",
            content_type="text/csv",
        )
        cls.current_row = DashboardData.objects.create(
            dashboard_slug="serology-statistics",
            source_file=cls.source_file,
            data={"chart": {}},
            uploaded_by="testuser",
            is_current=True,
        )
        cls.old_csv = SimpleUploadedFile(
            name="old.csv",
            content=b"date,value\n2023-01-01,50\n",
            content_type="text/csv",
        )
        DashboardData.objects.create(
            dashboard_slug="serology-statistics",
            source_file=cls.old_csv,
            data={"chart": {}},
            uploaded_by="testuser",
            is_current=False,
        )

    def test_returns_current_row(self) -> None:
        """Test that get_current returns the is_current=True row."""
        result = DashboardData.get_current("serology-statistics")
        self.assertEqual(result, self.current_row)

    def test_returns_none_for_missing_slug(self) -> None:
        """Test that get_current returns None when no data exists for slug."""
        result = DashboardData.get_current("nonexistent-dashboard")
        self.assertIsNone(result)


class TestDashboardDataMarkAsCurrent(TestCase):
    """Tests for the DashboardData.mark_as_current instance method."""

    def test_flips_previous_current_row(self) -> None:
        """Test that mark_as_current sets old row to is_current=False."""
        old_csv = SimpleUploadedFile("old.csv", b"a,b\n1,2\n", "text/csv")
        old_row = DashboardData.objects.create(
            dashboard_slug="serology-statistics",
            source_file=old_csv,
            data={},
            uploaded_by="testuser",
            is_current=True,
        )

        new_csv = SimpleUploadedFile("new.csv", b"a,b\n3,4\n", "text/csv")
        new_row = DashboardData.objects.create(
            dashboard_slug="serology-statistics",
            source_file=new_csv,
            data={},
            uploaded_by="testuser",
            is_current=False,
        )
        new_row.mark_as_current()

        old_row.refresh_from_db()
        self.assertFalse(old_row.is_current)
        self.assertTrue(new_row.is_current)

    def test_different_dashboards_do_not_interfere(self) -> None:
        """Test that mark_as_current only affects rows with the same slug."""
        vaccines_csv = SimpleUploadedFile("vaccines.csv", b"a,b\n1,2\n", "text/csv")
        vaccines_row = DashboardData.objects.create(
            dashboard_slug="vaccines",
            source_file=vaccines_csv,
            data={},
            uploaded_by="testuser",
            is_current=True,
        )

        serology_csv = SimpleUploadedFile("serology.csv", b"a,b\n3,4\n", "text/csv")
        serology_row = DashboardData.objects.create(
            dashboard_slug="serology-statistics",
            source_file=serology_csv,
            data={},
            uploaded_by="testuser",
            is_current=False,
        )
        serology_row.mark_as_current()

        vaccines_row.refresh_from_db()
        self.assertTrue(vaccines_row.is_current)
