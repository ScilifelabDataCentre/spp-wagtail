"""Tests for DashboardData model."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
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
            dashboard_title="Serology statistics",
            dashboard_slug="serology-statistics",
            source_file=cls.source_file,
            uploaded_by="testuser",
        )
        cls.dashboard_data.data = {"serology_chart": {"data": [], "layout": {}}}
        cls.dashboard_data.save(update_fields=["data"])

    def test_str_representation_includes_title(self) -> None:
        """Test that string representation includes the dashboard title."""
        result = str(self.dashboard_data)
        self.assertIn("Serology statistics", result)

    def test_ordering_is_by_slug(self) -> None:
        """Test that default ordering is by dashboard_slug."""
        self.assertEqual(DashboardData._meta.ordering, ["dashboard_slug"])

    def test_dashboard_slug_is_unique(self) -> None:
        """Test that only one row is allowed per dashboard_slug."""
        duplicate_file = SimpleUploadedFile("dup.csv", b"a,b\n1,2\n", "text/csv")
        with self.assertRaises(IntegrityError):
            DashboardData.objects.create(
                dashboard_slug="serology-statistics",
                source_file=duplicate_file,
                uploaded_by="testuser",
            )

    def test_source_file_upload_path(self) -> None:
        """Test that the source file is stored under dashboard_data/."""
        self.assertIn("dashboard_data/", self.dashboard_data.source_file.name)

    def test_data_field_stores_json(self) -> None:
        """Test that the data JSONField stores and retrieves correctly."""
        self.assertEqual(
            self.dashboard_data.data,
            {"serology_chart": {"data": [], "layout": {}}},
        )

    def test_data_updated_at_optional(self) -> None:
        """Test that data_updated_at can be set and saved independently."""
        from datetime import date

        self.dashboard_data.data_updated_at = date(2024, 6, 15)
        self.dashboard_data.save(update_fields=["data_updated_at"])
        self.dashboard_data.refresh_from_db()
        self.assertEqual(self.dashboard_data.data_updated_at, date(2024, 6, 15))


class TestDashboardDataGetData(TestCase):
    """Tests for the DashboardData.get_data class method."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Create a DashboardData row for lookup tests."""
        cls.source_file = SimpleUploadedFile(
            name="current.csv",
            content=b"date,value\n2024-01-01,100\n",
            content_type="text/csv",
        )
        cls.row = DashboardData.objects.create(
            dashboard_slug="serology-statistics",
            source_file=cls.source_file,
            data={"chart": {}},
            uploaded_by="testuser",
        )

    def test_returns_row_for_slug(self) -> None:
        """Test that get_data returns the row for a dashboard slug."""
        result = DashboardData.get_data("serology-statistics")
        self.assertEqual(result, self.row)

    def test_returns_none_for_missing_slug(self) -> None:
        """Test that get_data returns None when no data exists for slug."""
        result = DashboardData.get_data("nonexistent-dashboard")
        self.assertIsNone(result)
