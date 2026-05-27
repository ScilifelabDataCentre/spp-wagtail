"""CSV validation service for dashboard data uploads."""

import csv
import io
from dataclasses import dataclass, field
from typing import BinaryIO


@dataclass
class ValidationResult:
    """Result of CSV validation.

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


def validate_csv(file: BinaryIO, dashboard_slug: str) -> ValidationResult:
    """Validate an uploaded CSV file for a given dashboard.

    Checks that the file is a valid CSV, is not empty, and has at least
    one data row. Dashboard-specific column validation can be added per
    dashboard slug in the future.

    Args:
        file: The uploaded file object (binary mode).
        dashboard_slug: Identifies which dashboard schema to validate against.

    Returns:
        ValidationResult with is_valid flag and any errors.
    """
    try:
        content = file.read().decode("utf-8")
        file.seek(0)
    except UnicodeDecodeError, AttributeError:
        return ValidationResult(is_valid=False, errors=["File is not valid UTF-8 text."])

    if not content.strip():
        return ValidationResult(is_valid=False, errors=["File is empty."])

    try:
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
    except csv.Error as e:
        return ValidationResult(is_valid=False, errors=[f"CSV parsing error: {e}"])

    if len(rows) < 2:
        return ValidationResult(
            is_valid=False,
            errors=["CSV must have a header row and at least one data row."],
        )

    columns = rows[0]
    row_count = len(rows) - 1

    return ValidationResult(
        is_valid=True,
        errors=[],
        row_count=row_count,
        columns=columns,
    )
