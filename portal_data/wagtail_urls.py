"""Wagtail-facing URL routes for portal data file browsing."""

from django.urls import path

from .views import DownloadStudyFile, StudyFiles

app_name = "portal_data_wagtail"

DEFAULT = {"datatype": "metabolomics"}

urlpatterns = [
    path(
        "<slug:accession>/files/",
        StudyFiles.as_view(),
        DEFAULT,
        name="data_files",
    ),
    path(
        "<slug:accession>/files/<path:relpath>/",
        DownloadStudyFile.as_view(),
        DEFAULT,
        name="data_file",
    ),
]
