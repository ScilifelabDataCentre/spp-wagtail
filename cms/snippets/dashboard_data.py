"""Dashboard data storage snippet."""

from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet


class DashboardData(models.Model):
    """Stores uploaded CSV data and pre-computed Plotly figures for a dashboard.

    Each row represents one upload for a dashboard. The ``is_current`` flag marks
    which row is actively served on the public site. Previous rows are kept for
    rollback.

    All dashboards share this single table, differentiated by ``dashboard_slug``.
    The page reads the current row to render pre-computed Plotly charts, and
    serves the stored CSV file for visitor download.

    Attributes:
        dashboard_slug: Identifies which dashboard this data belongs to.
        csv_file: The uploaded CSV file, stored for visitor download and
            re-generation of figures when viz scripts change.
        data: Pre-computed Plotly figure JSON keyed by figure_id.
        uploaded_at: When the data was uploaded.
        uploaded_by: Username of the editor who uploaded.
        is_current: Whether this is the active row for this dashboard.
    """

    dashboard_slug = models.SlugField(max_length=255, db_index=True)
    csv_file = models.FileField(upload_to="dashboard_data/csv/")
    data = models.JSONField(default=dict, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=255, blank=True)
    is_current = models.BooleanField(default=True, db_index=True)

    panels = [
        FieldPanel(
            "dashboard_slug",
            help_text="Slug identifying which dashboard this data belongs to.",
        ),
        FieldPanel(
            "csv_file",
            help_text="CSV file containing the dashboard data.",
        ),
        FieldPanel(
            "is_current",
            help_text="Whether this is the active data row served on the public site.",
        ),
    ]

    class Meta:
        """Settings for the DashboardData model."""

        ordering = ["-uploaded_at"]
        verbose_name = "Dashboard data"
        verbose_name_plural = "Dashboard data"
        indexes = [
            models.Index(fields=["dashboard_slug", "is_current"]),
        ]

    def __str__(self) -> str:
        """Return slug and upload timestamp."""
        return f"{self.dashboard_slug} ({self.uploaded_at:%Y-%m-%d %H:%M})"

    def save(self, *args: object, **kwargs: object) -> None:
        """Generate Plotly figures from CSV on new uploads.

        If this is a new upload (csv_file present and data is empty), runs
        the viz service to populate the data JSONField. After saving, ensures
        this row is marked as current if is_current is True.
        """
        if self.csv_file and not self.data:
            from cms.services.dashboard_viz import generate_figures

            try:
                figures = generate_figures(self.dashboard_slug, self.csv_file.path)
                self.data = figures
            except (FileNotFoundError, ValueError):
                pass

        super().save(*args, **kwargs)

        if self.is_current:
            self.mark_as_current()

    @classmethod
    def get_current(cls, dashboard_slug: str) -> DashboardData | None:
        """Return the current data row for a dashboard, or None."""
        return cls.objects.filter(
            dashboard_slug=dashboard_slug, is_current=True
        ).first()

    def mark_as_current(self) -> None:
        """Mark this row as current and un-mark any previous current row."""
        DashboardData.objects.filter(
            dashboard_slug=self.dashboard_slug, is_current=True
        ).exclude(pk=self.pk).update(is_current=False)
        if not self.is_current:
            self.is_current = True
            self.save(update_fields=["is_current"])


class DashboardDataViewSet(SnippetViewSet):
    """Wagtail admin viewset for the DashboardData snippet.

    Controls the snippet list-view columns, ordering, and filtering.
    """

    model = DashboardData
    ordering = ["-uploaded_at"]
    list_display = ["dashboard_slug", "uploaded_at", "uploaded_by", "is_current"]
    list_filter = ["dashboard_slug", "is_current"]


register_snippet(DashboardDataViewSet)
