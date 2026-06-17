"""Manifest file for the portal data backend"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ManifestFile(BaseModel):
    name: str
    path: str
    size: int | None = None
    checksum: str | None = None


class ManifestProvenance(BaseModel):
    submitted_by: str
    submitted_at: datetime
    notes: str | None = None


class PortalBundleManifest(BaseModel):
    id: str
    title: str
    pathogen: str | None = None
    repository: str = "spp-unit-bundles"
    unit: str
    datatype: Literal["metabolomics"]
    year: int | None = None
    matrix: str | None = None
    instrument: str | None = None
    files: list[ManifestFile] = Field(default_factory=list)
    provenance: ManifestProvenance
    public: bool = False
    withdrawn: bool = False
    hidden: bool = False
