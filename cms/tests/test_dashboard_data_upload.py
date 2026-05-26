"""Tests for DashboardData CSV validation and viz service integration."""

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from cms.services.dashboard_data_validation import validate_csv
from cms.snippets.dashboard_data import DashboardData
from dashboard_viz import generate_figures


class TestCsvValidation(TestCase):
    """Tests for the CSV validation service."""

    def test_valid_csv_passes(self) -> None:
        """Test that a well-formed CSV with header and data passes."""
        content = b"date,value\n2024-01-01,100\n2024-01-02,200\n"
        file = BytesIO(content)
        result = validate_csv(file, "serology-statistics")

        self.assertTrue(result.is_valid)
        self.assertEqual(result.row_count, 2)
        self.assertEqual(result.columns, ["date", "value"])

    def test_empty_file_fails(self) -> None:
        """Test that an empty file fails validation."""
        file = BytesIO(b"")
        result = validate_csv(file, "serology-statistics")

        self.assertFalse(result.is_valid)
        self.assertIn("empty", result.errors[0].lower())

    def test_whitespace_only_file_fails(self) -> None:
        """Test that a file with only whitespace fails validation."""
        file = BytesIO(b"   \n  \n  ")
        result = validate_csv(file, "serology-statistics")

        self.assertFalse(result.is_valid)

    def test_header_only_fails(self) -> None:
        """Test that a CSV with only a header row fails."""
        file = BytesIO(b"date,value\n")
        result = validate_csv(file, "serology-statistics")

        self.assertFalse(result.is_valid)
        self.assertIn("header", result.errors[0].lower())

    def test_non_utf8_file_fails(self) -> None:
        """Test that a non-UTF-8 file fails validation."""
        file = BytesIO(b"\xff\xfe\x00\x01")
        result = validate_csv(file, "serology-statistics")

        self.assertFalse(result.is_valid)
        self.assertIn("UTF-8", result.errors[0])

    def test_file_seek_reset_after_validation(self) -> None:
        """Test that file position is reset after validation."""
        content = b"col1,col2\na,b\n"
        file = BytesIO(content)
        validate_csv(file, "test-dashboard")

        self.assertEqual(file.tell(), 0)


class TestGenerateFigures(TestCase):
    """Tests for the viz service registry."""

    def test_unregistered_slug_returns_empty_dict(self) -> None:
        """Test that an unregistered dashboard slug returns empty dict."""
        result = generate_figures("nonexistent-dashboard", "/fake/path.csv")
        self.assertEqual(result, {})

    def test_returns_dict_type(self) -> None:
        """Test that generate_figures always returns a dict."""
        result = generate_figures("unknown-slug", "/any/path.csv")
        self.assertIsInstance(result, dict)


class TestDashboardDataSaveIntegration(TestCase):
    """Tests for DashboardData save hook with viz service integration."""

    def test_save_with_no_registered_service_keeps_empty_data(self) -> None:
        """Test that saving with unregistered slug keeps data as empty dict."""
        csv_file = SimpleUploadedFile("test.csv", b"a,b\n1,2\n", "text/csv")
        row = DashboardData.objects.create(
            dashboard_slug="unregistered-dashboard",
            csv_file=csv_file,
            uploaded_by="testuser",
            is_current=True,
        )
        self.assertEqual(row.data, {})

    def test_save_marks_as_current(self) -> None:
        """Test that saving with is_current=True marks previous rows as not current."""
        csv1 = SimpleUploadedFile("old.csv", b"a,b\n1,2\n", "text/csv")
        old_row = DashboardData.objects.create(
            dashboard_slug="test-dashboard",
            csv_file=csv1,
            uploaded_by="testuser",
            is_current=True,
        )

        csv2 = SimpleUploadedFile("new.csv", b"a,b\n3,4\n", "text/csv")
        DashboardData.objects.create(
            dashboard_slug="test-dashboard",
            csv_file=csv2,
            uploaded_by="testuser",
            is_current=True,
        )

        old_row.refresh_from_db()
        self.assertFalse(old_row.is_current)
