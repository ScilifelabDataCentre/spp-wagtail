"""Base file for the portal data backend"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PortalDataFile:
    name: str
    path: str
    size: int | None = None
    checksum: str | None = None


@dataclass(frozen=True)
class PortalDataset:
    id: str
    title: str
    datatype: str
    repository: str
    year: int | None
    unit: str | None
    metadata: dict
    files: list[PortalDataFile]


class PortalDataBackend(Protocol):
    def list_datasets(self, *, datatype: str) -> list[PortalDataset]: ...

    def get_dataset(self, dataset_id: str) -> PortalDataset | None: ...

    def get_download_url(
        self,
        *,
        dataset_id: str,
        file_path: str,
        expires_in_seconds: int,
    ) -> str: ...
