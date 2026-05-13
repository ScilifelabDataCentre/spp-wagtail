"""Wagtail admin form subclasses used by ``base_form_class`` on page models."""

from .plp_project import PlpProjectPageCopyForm, PlpProjectPageForm

__all__ = [
    "PlpProjectPageCopyForm",
    "PlpProjectPageForm",
]
