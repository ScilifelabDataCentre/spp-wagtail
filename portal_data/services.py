"""Service functions for portal data listing, facets, exports, and file browsing."""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import nh3
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

_ALLOWED_TAGS = {"p", "br", "strong", "em", "a", "ul", "ol", "li"}
_ALLOWED_ATTRIBUTES: dict[str, set[str]] = {"a": {"href", "target"}}


@dataclass(frozen=True)
class DataTypeConfig:
    """Configuration for a supported portal data type."""

    label: str
    default_facets: tuple[str, ...]


SUPPORTED_TYPES: dict[str, DataTypeConfig] = {
    "metabolomics": DataTypeConfig(
        label="Metabolomics",
        default_facets=(
            "year",
            "platforms",
            "technology",
            "factors",
            "design_types",
            "repository",
        ),
    ),
}

ACCESSION_RE = re.compile(r"^MTBLS\d+$")

EXPORT_FIELDS: list[tuple[str, str]] = [
    ("id", "Accession"),
    ("title", "Title"),
    ("pathogen", "Pathogen"),
    ("matrix", "Matrix"),
    ("instrument", "Instrument"),
    ("country", "Country"),
    ("year", "Year"),
    ("repository", "Repository"),
    ("repo_url", "Repository URL"),
]


def _clean_html(raw: str) -> str:
    """Strip unsafe tags from HTML, keeping a safe presentational subset."""
    sanitized_html = nh3.clean(
        raw,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        link_rel=None,
    )
    if sanitized_html:
        sanitized_html = re.sub(
            r"<p>\s*(<br\s*/?>\s*)*</p>",
            "",
            sanitized_html,
            flags=re.IGNORECASE,
        )
    return sanitized_html


def get_datatype_config(datatype: object) -> DataTypeConfig | None:
    """Return configuration for a supported data type, if available."""
    normalized = str(datatype or "").strip().lower()
    return SUPPORTED_TYPES.get(normalized)


def get_dataset_listing(
    *,
    datatype: str,
    query: str,
    filters: dict[str, list[str]],
    facet_names: list[str],
) -> dict[str, Any]:
    """Return filtered studies and facets for the listing page."""
    all_items = load_all_items(datatype)

    searched_items = apply_text_search(all_items, query)
    filtered_items = apply_facet_filters(searched_items, filters)

    facets = build_facets(
        items=searched_items,
        facet_names=facet_names,
        filters=filters,
        datatype=datatype,
    )

    return {
        "items": filtered_items,
        "facets": facets,
        "has_facets": any(bool(facet["buckets"]) for facet in facets),
    }


def get_data_root() -> Path:
    """Return the configured datasets root.

    Calculated at call time so tests and environment overrides work correctly.
    """
    return Path(settings.DATASETS_ROOT).expanduser().resolve()


def _normalize_items(items: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """Normalize view items for export."""
    normalized: list[dict[str, object]] = []

    for item in items:
        row: dict[str, object] = {}
        for key, _label in EXPORT_FIELDS:
            value = item.get(key, "")
            row[key] = "" if value is None else value
        normalized.append(row)

    return normalized


def build_export_tsv(
    items: Iterable[Mapping[str, object]],
    default_filename: str = "export.tsv",
) -> tuple[str, str, str]:
    """Build a TSV export from a sequence of item dictionaries."""
    rows = _normalize_items(items)

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t")
    writer.writerow([label for _key, label in EXPORT_FIELDS])

    for row in rows:
        writer.writerow([row.get(key, "") for key, _label in EXPORT_FIELDS])

    content = buffer.getvalue()
    buffer.close()

    filename = default_filename or "export.tsv"
    content_type = "text/tab-separated-values; charset=utf-8"
    return content, filename, content_type


def build_export_json(
    items: Iterable[Mapping[str, object]],
    default_filename: str = "export.json",
) -> tuple[str, str, str]:
    """Build a JSON export from a sequence of item dictionaries."""
    rows = _normalize_items(items)
    content = json.dumps(rows, indent=2, ensure_ascii=False)

    filename = default_filename or "export.json"
    content_type = "application/json; charset=utf-8"
    return content, filename, content_type


def _iter_study_dirs(datatype: str) -> list[Path]:
    """Return directories that look like MetaboLights studies."""
    if datatype != "metabolomics":
        return []

    data_root = get_data_root()
    if not data_root.exists():
        return []

    candidates: dict[str, Path] = {}

    for path in data_root.iterdir():
        if not path.is_dir():
            continue

        name = path.name
        if not name.startswith("MTBLS"):
            continue

        suffix = name[5:]
        if not suffix.isdigit():
            continue

        candidates[name] = path

    return [candidates[name] for name in sorted(candidates)]


def load_all_items(datatype: str) -> list[dict[str, Any]]:
    """Load all public metabolomics datasets from the local/PVC data root.

    StorageGRID-backed loading should be added later behind this public function,
    preferably controlled by a feature flag such as PORTAL_DATA_SOURCE.
    """
    datatype = str(datatype or "").strip().lower()

    if datatype != "metabolomics":
        return []

    items: list[dict[str, Any]] = []

    for study_dir in _iter_study_dirs(datatype):
        accession = study_dir.name
        inv_path = find_investigation_file(study_dir)
        meta = parse_investigation_file(inv_path)

        title = str(meta.get("study_title") or accession)
        description = _clean_html(str(meta.get("study_description") or ""))

        public_release = meta.get("study_public_release_date")
        year = None
        if isinstance(public_release, str) and len(public_release) >= 4:
            year = public_release[:4]

        item = {
            "id": accession,
            "accession": accession,
            "title": title,
            "pathogen": "",
            "matrix": "",
            "instrument": "",
            "country": "",
            "year": year,
            "repository": "MetaboLights",
            "repo_accession": accession,
            "repo_url": f"https://www.ebi.ac.uk/metabolights/{accession}",
            "description": description,
            "tags": meta.get("tags", []),
            "public_release_date": public_release,
            "submission_date": meta.get("study_submission_date"),
            "license": meta.get("license"),
            "factors": meta.get("factors", []),
            "design_types": meta.get("design_types", []),
            "platforms": meta.get("platforms", []),
            "publication_title": meta.get("publication_title"),
            "publication_doi": meta.get("publication_doi"),
            "publication_authors": meta.get("publication_authors"),
            "technology": meta.get("technology"),
            "local_path": str(study_dir),
        }
        items.append(item)

    return items


def apply_text_search(items: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    """Apply text search to dataset listing items."""
    if not query:
        return items

    normalized_query = query.lower()

    def matches_text(item: dict[str, Any]) -> bool:
        searchable_fields = (
            item.get("title", ""),
            item.get("id", ""),
            item.get("accession", ""),
            item.get("description", ""),
        )

        if any(normalized_query in str(value).lower() for value in searchable_fields):
            return True

        tags = item.get("tags", [])
        if isinstance(tags, str):
            return normalized_query in tags.lower()

        return any(normalized_query in str(tag).lower() for tag in tags)

    return [item for item in items if matches_text(item)]


def apply_facet_filters(
    items: list[dict[str, Any]],
    filters: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Apply selected facet filters to dataset listing items."""
    if not filters:
        return items

    filtered_items = items

    for field, values in filters.items():
        if not values:
            continue

        selected_values = {str(value) for value in values}

        def matches_filter(
            item: dict[str, Any],
            *,
            field_name: str = field,
            allowed_values: set[str] = selected_values,
        ) -> bool:
            field_value = item.get(field_name)

            if field_value in (None, "", [], {}):
                return False

            if isinstance(field_value, list):
                return any(
                    str(value) in allowed_values
                    for value in field_value
                    if value not in (None, "")
                )

            return str(field_value) in allowed_values

        filtered_items = [item for item in filtered_items if matches_filter(item)]

    return filtered_items


def apply_search_and_filters(
    items: list[dict[str, Any]],
    query: str,
    filters: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Apply text search followed by facet filters."""
    return apply_facet_filters(apply_text_search(items, query), filters)


def _facet_label(field: str) -> str:
    """Return a display label for a facet field."""
    return field.replace("_", " ").capitalize()


def build_facets(
    items: list[dict[str, Any]],
    facet_names: list[str],
    filters: dict[str, list[str]] | None,
    datatype: str,
) -> list[dict[str, Any]]:
    """Build facet groups for the listing template."""
    del datatype

    filters = filters or {}
    facet_groups: list[dict[str, Any]] = []

    for facet in facet_names:
        counts: dict[str, int] = {}

        for item in items:
            value = item.get(facet)

            if value in (None, "", [], {}):
                continue

            if isinstance(value, list):
                for entry in value:
                    if entry not in (None, ""):
                        key = str(entry)
                        counts[key] = counts.get(key, 0) + 1
            else:
                key = str(value)
                counts[key] = counts.get(key, 0) + 1

        buckets = list(counts.items())

        if facet == "year" and buckets:

            def is_integer_string(value: str) -> bool:
                return re.fullmatch(r"-?\d+", value) is not None

            if all(is_integer_string(key) for key, _count in buckets):
                buckets.sort(key=lambda item: int(item[0]), reverse=True)
            else:
                buckets.sort(key=lambda item: item[0], reverse=True)
        else:
            buckets.sort(key=lambda item: item[0])

        active_values = set(filters.get(facet, []))
        facet_groups.append(
            {
                "field": facet,
                "label": _facet_label(facet),
                "buckets": [
                    {
                        "value": value,
                        "count": count,
                        "checked": str(value) in active_values,
                    }
                    for value, count in buckets
                ],
            }
        )

    return facet_groups


def find_investigation_file(study_dir: Path) -> Path | None:
    """Find the preferred investigation file for a study directory."""
    revisions_root = study_dir / "METADATA_REVISIONS"

    if revisions_root.is_dir():
        revision_dirs = sorted(
            [path for path in revisions_root.iterdir() if path.is_dir()],
            key=lambda path: path.name,
        )

        for revision_dir in reversed(revision_dirs):
            candidate = revision_dir / "i_Investigation.txt"
            if candidate.is_file():
                return candidate

    candidate = study_dir / "i_Investigation.txt"
    if candidate.is_file():
        return candidate

    return None


def parse_investigation_file(path: Path | None) -> dict[str, object]:
    """Parse selected study metadata from an ISA-tab investigation file."""
    meta: dict[str, object] = {}

    if path is None or not path.is_file():
        return meta

    try:
        with path.open(encoding="utf-8") as file_obj:
            for raw_line in file_obj:
                line = raw_line.rstrip("\n")
                if not line or "\t" not in line:
                    continue

                columns = [column.strip() for column in line.split("\t")]
                key = columns[0]
                values = [column for column in columns[1:] if column]

                if not values:
                    continue

                if key == "Study Title":
                    meta["study_title"] = values[0]
                elif key == "Study Description":
                    meta["study_description"] = values[0]
                elif key == "Study Submission Date":
                    meta["study_submission_date"] = values[0]
                elif key == "Study Public Release Date":
                    meta["study_public_release_date"] = values[0]
                elif key == "Comment[License]":
                    meta["license"] = values[0]
                elif key == "Study Publication Title":
                    meta["publication_title"] = values[0]
                elif key == "Study Publication DOI":
                    meta["publication_doi"] = values[0]
                elif key == "Study Publication Author List":
                    meta["publication_authors"] = values[0]
                elif key == "Study Factor Name":
                    meta["factors"] = values
                elif key == "Study Design Type":
                    meta["design_types"] = values
                elif key == "Study Assay Technology Platform":
                    meta["platforms"] = values
                elif key == "Study Assay Technology Type":
                    meta["technology"] = values[0]
    except FileNotFoundError:
        logger.debug("Investigation file disappeared during parsing: %s", path)

    return meta


def list_study_files(study_dir: Path) -> list[dict[str, Any]]:
    """List all files within a study directory."""
    files: list[dict[str, Any]] = []

    for root, _dirnames, filenames in os.walk(study_dir):
        for filename in filenames:
            full_path = Path(root) / filename

            try:
                relpath = str(full_path.relative_to(study_dir)).replace(os.sep, "/")
                stat = full_path.stat()
            except (OSError, ValueError):
                logger.debug("Skipping file during listing: %s", full_path, exc_info=True)
                continue

            files.append(
                {
                    "relpath": relpath,
                    "name": filename,
                    "size": stat.st_size,
                    "mtime": datetime.fromtimestamp(
                        stat.st_mtime,
                        tz=timezone.get_current_timezone(),
                    ),
                }
            )

    files.sort(key=lambda file_info: file_info["relpath"])
    return files
