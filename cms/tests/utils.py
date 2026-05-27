"""Utility functions for testing."""

import csv
import io
from dataclasses import dataclass, field
from typing import BinaryIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage
from wagtail.images import get_image_model


@dataclass
class CsvValidationResult:
    """Result of CSV validation in tests.

    Attributes:
        is_valid: Whether the CSV passed validation.
        errors: List of validation error messages.
        row_count: Number of data rows in the CSV.
        columns: List of column names found in the CSV.
    """

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    row_count: int = 0
    columns: list[str] = field(default_factory=list)


def validate_csv(file: BinaryIO) -> CsvValidationResult:
    """Validate an uploaded CSV file (generic checks for tests).

    Checks that the file is valid UTF-8 CSV, is not empty, and has at least
    one data row. Not used in production yet; intended to be wired into
    ``DashboardData`` upload validation when dashboard-specific schemas exist.
    """
    try:
        content = file.read().decode("utf-8")
        file.seek(0)
    except UnicodeDecodeError, AttributeError:
        return CsvValidationResult(is_valid=False, errors=["File is not valid UTF-8 text."])

    if not content.strip():
        return CsvValidationResult(is_valid=False, errors=["File is empty."])

    try:
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
    except csv.Error as e:
        return CsvValidationResult(is_valid=False, errors=[f"CSV parsing error: {e}"])

    if len(rows) < 2:
        return CsvValidationResult(
            is_valid=False,
            errors=["CSV must have a header row and at least one data row."],
        )

    columns = rows[0]
    row_count = len(rows) - 1

    return CsvValidationResult(
        is_valid=True,
        errors=[],
        row_count=row_count,
        columns=columns,
    )


def create_test_image(*, title: str = "Test image", file_name: str = "test.jpg"):
    """Create and save a minimal test image for use in tests.

    Args:
        title (str): The title for the image.
        file_name (str): The file name for the image.

    Example usage:
        image = create_test_image(title="My Test Image", file_name="my_test_image.jpg")

    Returns:
        Image: A saved Wagtail Image model instance.
    """
    file_obj = io.BytesIO()

    image = PILImage.new("RGB", (1, 1), color="white")
    image.save(file_obj, format="JPEG")

    file_obj.seek(0)

    Image = get_image_model()  # noqa: N806
    return Image.objects.create(
        title=title,
        file=SimpleUploadedFile(
            name=file_name,
            content=file_obj.read(),
            content_type="image/jpeg",
        ),
    )
