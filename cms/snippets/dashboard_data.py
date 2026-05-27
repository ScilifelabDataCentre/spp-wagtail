"""Dashboard data upload snippet."""

import structlog
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.models import RevisionMixin
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from dashboard_viz.utils.file_hash import calculate_file_hash

LOGGER = structlog.get_logger(__name__)


class DashboardData(RevisionMixin, models.Model):
    """Stores uploaded data and pre-computed Plotly figures for a dashboard.

    One row per dashboard (``dashboard_slug`` is unique). Wagtail revisions
    (via ``RevisionMixin``) provide history and rollback instead of duplicate rows.

    Attributes:
        dashboard_title: Human-readable title for admin display.
        dashboard_slug: Unique identifier matching the dashboard page slug.
        source_file: The uploaded source data file (CSV, Excel, etc.), stored
            for visitor download and re-generation of figures when viz scripts change.
        source_file_hash: SHA-256 of ``source_file``; used to detect file changes.
        data: Pre-computed Plotly figure JSON keyed by figure_id.
        data_updated_at: Public-facing date for when the underlying data was last updated.
            Set automatically to today when ``source_file`` changes; editors can override.
        uploaded_at: Automatic timestamp when this row was first saved in Wagtail (audit only).
        uploaded_by: Username of the editor who uploaded.
    """

    dashboard_title = models.CharField(
        max_length=255,
        default="",
        help_text="Human-readable dashboard name for admin display.",
    )
    dashboard_slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text="Must match the dashboard page slug. One data upload per dashboard.",
    )
    source_file = models.FileField(upload_to="dashboard_data/")
    source_file_hash = models.CharField(max_length=64, blank=True, editable=False)
    data = models.JSONField(default=dict, blank=True)
    data_updated_at = models.DateField(
        null=True,
        blank=True,
        help_text=(
            "Date shown on the public dashboard as when the underlying data was last updated. "
            "Updates automatically to today when the source file is replaced; you can override "
            "manually (e.g. historic migration date)."
        ),
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this row was first saved in Wagtail (audit only; not public freshness).",
    )
    uploaded_by = models.CharField(max_length=255, blank=True)
    revisions = GenericRelation("wagtailcore.Revision", related_query_name="dashboarddata")

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("dashboard_title"),
                FieldPanel("dashboard_slug"),
            ],
            heading="Dashboard",
        ),
        FieldPanel(
            "source_file",
            help_text="Source data file (CSV, Excel, etc.) for this dashboard.",
        ),
        FieldPanel("data_updated_at"),
        FieldPanel(
            "data",
            help_text=(
                "Pre-computed Plotly figure JSON keyed by figure_id. "
                "Auto-regenerated when the source file changes, "
                "or paste JSON directly for historic dashboards."
            ),
        ),
    ]

    class Meta:
        """Settings for the DashboardData model."""

        ordering = ["dashboard_slug"]
        verbose_name = "Dashboard data upload"
        verbose_name_plural = "Dashboard data uploads"

    def __str__(self) -> str:
        """Return title and upload timestamp."""
        return f"{self.dashboard_title} ({self.uploaded_at:%Y-%m-%d %H:%M})"

    def save(self, *args: object, **kwargs: object) -> None:
        """Persist the row and regenerate figures when the source file changes."""
        file_changed = False

        if self.source_file:
            new_hash = calculate_file_hash(self.source_file)

            if self.pk:
                old_hash = (
                    type(self)
                    .objects.filter(pk=self.pk)
                    .values_list("source_file_hash", flat=True)
                    .first()
                )
                file_changed = old_hash != new_hash
            else:
                file_changed = True

            self.source_file_hash = new_hash

        if file_changed:
            self.data_updated_at = timezone.localdate()
            from dashboard_viz import generate_figures

            try:
                figures = generate_figures(self.dashboard_slug, self.source_file)
                self.data = figures or {}
            except (FileNotFoundError, ValueError) as exc:
                LOGGER.warning(
                    "dashboard_data.generate_figures_failed",
                    dashboard_slug=self.dashboard_slug,
                    error=str(exc),
                )

        super().save(*args, **kwargs)

    @classmethod
    def get_current(cls, dashboard_slug: str) -> DashboardData | None:
        """Return the data row for a dashboard slug, or None."""
        try:
            return cls.objects.get(dashboard_slug=dashboard_slug)
        except cls.DoesNotExist:
            return None


class DashboardDataViewSet(SnippetViewSet):
    """Wagtail admin viewset for the Dashboard Data Upload snippet."""

    model = DashboardData
    icon = "doc-full-inverse"
    menu_label = "Dashboard Data Upload"
    menu_name = "dashboard-data-upload"
    ordering = ["dashboard_slug"]
    list_display = [
        "dashboard_title",
        "dashboard_slug",
        "data_updated_at",
        "uploaded_at",
        "uploaded_by",
    ]
    list_filter = ["dashboard_slug"]


register_snippet(DashboardDataViewSet)
