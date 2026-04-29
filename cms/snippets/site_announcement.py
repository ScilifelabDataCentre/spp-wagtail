"""Site announcement snippet."""

from django.db import models
from django.db.models import F
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet


class SiteAnnouncement(models.Model):
    """A site-wide announcement rendered above the page header on every public page.

    Editors toggle `is_enabled` to surface or hide a banner and reorder banners by
    drag-and-drop in the admin list view (powered by ``sort_order_field`` on the
    viewset). The `announcement_type` choice drives the DaisyUI alert colour in
    the public template (maintenance → `alert-warning`, survey → `alert-info`).

    Attributes:
        title (str): Short internal label used in the admin list view.
        message (str): Rich-text body rendered inside the banner. Features are
            restricted to `bold`, `italic`, and `link` — no headings, no lists.
        announcement_type (str): One of `maintenance` or `survey`; selects the
            DaisyUI alert colour.
        is_enabled (bool): When False the banner is not rendered on public pages.
        sort_order (int): Ascending display order when multiple enabled banners
            are rendered. Managed by Wagtail's drag-and-drop interface; ties
            are broken by primary key.
    """

    ANNOUNCEMENT_TYPE_CHOICES = [
        ("maintenance", "Maintenance"),
        ("survey", "Survey"),
    ]

    title = models.CharField(max_length=255)
    message = RichTextField(features=["bold", "italic", "link"])
    announcement_type = models.CharField(
        max_length=20,
        choices=ANNOUNCEMENT_TYPE_CHOICES,
    )
    is_enabled = models.BooleanField(default=False)
    sort_order = models.IntegerField(null=True, blank=True, editable=False, db_index=True)

    panels = [
        FieldPanel(
            "title",
            help_text=(
                "Internal label shown only in the admin list. Not rendered on the public site."
            ),
        ),
        FieldPanel(
            "message",
            help_text=(
                "Banner copy. Bold, italic, and links are allowed; headings and lists are not."
            ),
        ),
        FieldPanel(
            "announcement_type",
            help_text=(
                "Selects the banner colour and icon. Maintenance shows yellow with a warning "
                "triangle; survey shows blue with an info circle."
            ),
        ),
        FieldPanel(
            "is_enabled",
            help_text=(
                "When enabled, the banner is shown above the page header on every public page."
            ),
        ),
    ]

    class Meta:
        """Settings for the site announcement snippet."""

        ordering = ["sort_order", "-pk"]
        verbose_name = "Site announcement"
        verbose_name_plural = "Site announcements"

    def __str__(self) -> str:
        """Return a human-readable representation."""
        return self.title

    def save(self, *args: object, **kwargs: object) -> None:
        """Insert new announcements at the top of the list."""
        if self._state.adding and self.sort_order is None:
            SiteAnnouncement.objects.update(sort_order=F("sort_order") + 1)
            self.sort_order = 0
        super().save(*args, **kwargs)


class SiteAnnouncementViewSet(SnippetViewSet):
    """Wagtail admin viewset for the `SiteAnnouncement` snippet.

    Controls the snippet list-view columns and the default admin ordering.
    Setting ``sort_order_field`` exposes the "Sort item order" toggle on
    the index view, which activates Wagtail's drag-and-drop interface so
    editors reorder banners visually instead of editing the integer
    ``sort_order`` by hand.
    """

    model = SiteAnnouncement
    ordering = ["sort_order", "-pk"]
    sort_order_field = "sort_order"
    list_display = ["title", "announcement_type", "is_enabled", "sort_order"]


register_snippet(SiteAnnouncementViewSet)
