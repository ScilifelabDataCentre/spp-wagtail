"""Tests for portal_data views."""

from __future__ import annotations

import tempfile
from pathlib import Path

from django.test import TestCase, override_settings
from django.urls import reverse


def write_investigation_file(study_dir: Path) -> None:
    """Write a minimal investigation file for a test study."""
    study_dir.mkdir(parents=True, exist_ok=True)
    (study_dir / "i_Investigation.txt").write_text(
        "\n".join(
            [
                "Study Title\tExample study",
                "Study Public Release Date\t2024-01-01",
                "Study Assay Technology Platform\tLC-MS",
            ]
        ),
        encoding="utf-8",
    )


class PortalDataViewTests(TestCase):
    """Tests for file browser and download views."""

    def setUp(self) -> None:
        """Create a temporary dataset root for each test."""
        self.tmpdir_context = tempfile.TemporaryDirectory()
        self.datasets_root = Path(self.tmpdir_context.name)

    def tearDown(self) -> None:
        """Remove the temporary dataset root."""
        self.tmpdir_context.cleanup()

    def test_study_files_uses_configured_portal_data_index_url(self) -> None:
        """Use the configured canonical index URL in the file browser."""
        study_dir = self.datasets_root / "MTBLS1001"
        write_investigation_file(study_dir)
        (study_dir / "example.tsv").write_text("a\tb\n", encoding="utf-8")

        with override_settings(
            DATASETS_ROOT=self.datasets_root,
            PORTAL_DATA_INDEX_URL="/data/",
        ):
            url = reverse(
                "portal_data:data_files",
                kwargs={"accession": "MTBLS1001"},
            )
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/data/"', response.content)

    def test_download_study_file_streams_existing_file(self) -> None:
        """Stream an existing study file from the PVC-backed study directory."""
        study_dir = self.datasets_root / "MTBLS1001"
        write_investigation_file(study_dir)
        (study_dir / "example.tsv").write_text("a\tb\n", encoding="utf-8")

        with override_settings(DATASETS_ROOT=self.datasets_root):
            url = reverse(
                "portal_data:data_file",
                kwargs={
                    "accession": "MTBLS1001",
                    "relpath": "example.tsv",
                },
            )
            response = self.client.get(url)

        valid_content_types = (
            "text/tab-separated-values",
            "text/plain",
            "application/octet-stream",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response["Content-Type"].startswith(valid_content_types),
        )

    def test_download_rejects_path_traversal(self) -> None:
        """Reject download paths that attempt to escape the study directory."""
        study_dir = self.datasets_root / "MTBLS1001"
        write_investigation_file(study_dir)

        outside_file = self.datasets_root / "secret.txt"
        outside_file.write_text("secret", encoding="utf-8")

        with override_settings(DATASETS_ROOT=self.datasets_root):
            response = self.client.get(
                "/portal-data/MTBLS1001/files/%2E%2E/secret.txt/",
            )

        self.assertEqual(response.status_code, 404)
