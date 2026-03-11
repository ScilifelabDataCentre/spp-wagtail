"""Configuration for the cms app."""

from django.apps import AppConfig


class CommonConfig(AppConfig):
    """Configuration for the cms app.

    This app consists of wagtail cms page models, components, etc.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "cms"
    verbose_name = "cms"
