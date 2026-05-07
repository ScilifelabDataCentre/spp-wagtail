"""Tests for portal data service helpers."""

from pathlib import Path
from unittest import TestCase

from django.conf import LazySettings

from portal_data.services import load_all_items, parse_investigation_file


def test_parse_investigation_file_extracts_study_metadata(tmp_path: Path) -> None:
    """Parse study metadata fields from an ISA investigation file."""
    investigation = tmp_path / "i_Investigation.txt"
    investigation.write_text(
        "\n".join(
            [
                "Study Title\tExample metabolomics study",
                "Study Description\tA useful description.",
                "Study Public Release Date\t2024-01-15",
                "Study Factor Name\tTreatment\tTimepoint",
                "Study Design Type\tcase control design",
                "Study Assay Technology Platform\tLC-MS",
                "Study Assay Technology Type\tmass spectrometry",
            ]
        ),
        encoding="utf-8",
    )

    meta = parse_investigation_file(investigation)
    test_case = TestCase()

    test_case.assertEqual(meta["study_title"], "Example metabolomics study")
    test_case.assertEqual(meta["study_description"], "A useful description.")
    test_case.assertEqual(meta["study_public_release_date"], "2024-01-15")
    test_case.assertEqual(meta["factors"], ["Treatment", "Timepoint"])
    test_case.assertEqual(meta["design_types"], ["case control design"])
    test_case.assertEqual(meta["platforms"], ["LC-MS"])
    test_case.assertEqual(meta["technology"], "mass spectrometry")


def test_load_all_items_reads_valid_metabolights_dirs(
    tmp_path: Path,
    settings: LazySettings,
) -> None:
    """Load only valid MetaboLights study directories from the dataset root."""
    settings.DATASETS_ROOT = tmp_path

    study = tmp_path / "MTBLS9999"
    study.mkdir()
    (study / "i_Investigation.txt").write_text(
        "Study Title\tExample study\n"
        "Study Public Release Date\t2024-01-15\n",
        encoding="utf-8",
    )

    ignored = tmp_path / "not-a-study"
    ignored.mkdir()

    items = load_all_items("metabolomics")
    test_case = TestCase()

    test_case.assertEqual(len(items), 1)
    test_case.assertEqual(items[0]["accession"], "MTBLS9999")
    test_case.assertEqual(items[0]["title"], "Example study")
    test_case.assertEqual(items[0]["year"], "2024")
