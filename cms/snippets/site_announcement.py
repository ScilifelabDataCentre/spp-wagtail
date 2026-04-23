"""Site announcement snippet."""

from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet


class SiteAnnouncement(models.Model):
    """A site-wide announcement rendered above the page header on every public page.

    Editors toggle `is_enabled` to surface or hide a banner and reorder banners by
    editing the integer `sort_order` in the admin list view. The `announcement_type`
    choice drives the DaisyUI alert colour in the public template (maintenance →
    `alert-warning`, survey → `alert-info`).

    Attributes:
        title (str): Short internal label used in the admin list view.
        message (str): Rich-text body rendered inside the banner. Features are
            restricted to `bold`, `italic`, and `link` — no headings, no lists.
        announcement_type (str): One of `maintenance` or `survey`; selects the
            DaisyUI alert colour.
        is_enabled (bool): When False the banner is not rendered on public pages.
        sort_order (int): Ascending display order when multiple enabled banners
            are rendered. Ties are broken by primary key.
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
    sort_order = models.PositiveIntegerField(default=0)

    panels = [
        FieldPanel("title"),
        FieldPanel("message"),
        FieldPanel("announcement_type"),
        FieldPanel("is_enabled"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        """Settings for the site announcement snippet."""

        ordering = ["sort_order", "pk"]
        verbose_name = "Site announcement"
        verbose_name_plural = "Site announcements"

    def __str__(self) -> str:
        """Return a human-readable representation."""
        return self.title


class SiteAnnouncementViewSet(SnippetViewSet):
    """Wagtail admin viewset for the `SiteAnnouncement` snippet.

    Controls the snippet list-view columns and the default admin ordering so
    editors can reorder banners by editing the integer `sort_order` directly.
    """

    model = SiteAnnouncement
    ordering = ["sort_order"]
    list_display = ["title", "announcement_type", "is_enabled", "sort_order"]


register_snippet(SiteAnnouncementViewSet)
