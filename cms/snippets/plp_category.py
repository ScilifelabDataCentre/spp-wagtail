"""PLP category snippet."""

from django.db import models
from django.utils.text import slugify
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.chooser import (
    ChooseResultsView,
    ChooseView,
    SnippetChooserViewSet,
)
from wagtail.snippets.views.snippets import SnippetViewSet

_CHOOSER_RESULTS_TEMPLATE = "cms/admin/plp_category_chooser_results.html"


class PlpCategory(models.Model):
    """Editor-managed category for grouping PLP project pages on the index.

    Each ``PlpCategory`` represents a labelled group on the
    Pandemic Laboratory Preparedness landing page (e.g. "Pandemic Laboratory
    Preparedness Capabilities round 1"). Categories are referenced by
    ``PlpProjectPage`` via a protected foreign key; the index renders a card
    section per category in ``(order, title)`` order so editors can add new
    rounds (PLP3, future TDP calls, …) without code changes.

    Attributes:
        title (str): Short admin-facing label used in dropdowns and listings.
        slug (str): Stable identifier auto-generated from ``title`` when left
            blank in admin; used in URLs and template lookups.
        group_label (str): Public-facing section heading rendered above the
            category's project cards on the index page.
        order (int): Ascending sort key controlling section order on the
            index; ties are broken by ``title``.
    """

    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    group_label = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    panels = [
        FieldPanel("title", help_text="Short admin label (e.g. 'PLP1', 'TDP')."),
        FieldPanel(
            "slug",
            help_text="URL-friendly identifier; auto-generated from title if left blank.",
        ),
        FieldPanel(
            "group_label",
            help_text="Public-facing section heading shown above this category's cards.",
        ),
        FieldPanel(
            "order",
            help_text="Lower values appear first on the index page; ties broken by title.",
        ),
    ]

    class Meta:
        """Settings for the PLP category snippet."""

        ordering = ["order", "title"]
        verbose_name = "PLP category"
        verbose_name_plural = "PLP categories"

    def __str__(self) -> str:
        """Return a human-readable representation."""
        return self.title

    def save(self, *args: object, **kwargs: object) -> None:
        """Auto-generate slug from title if not provided."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Populate slug from title before uniqueness validation when blank."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().clean()


class _PlpCategoryChooseView(ChooseView):
    results_template_name = _CHOOSER_RESULTS_TEMPLATE


class _PlpCategoryChooseResultsView(ChooseResultsView):
    results_template_name = _CHOOSER_RESULTS_TEMPLATE


class PlpCategoryChooserViewSet(SnippetChooserViewSet):
    """Chooser viewset that adds a 'Create new PLP category' link above results.

    The default snippet chooser only shows a create affordance when the listing
    is empty. Swapping the results template adds a link to the snippet's add
    view at the top of the listing so editors can jump out and create another
    category when entries already exist; the empty-state link from the parent
    template is preserved.
    """

    choose_view_class = _PlpCategoryChooseView
    choose_results_view_class = _PlpCategoryChooseResultsView


class PlpCategoryViewSet(SnippetViewSet):
    """Snippet viewset wiring the custom chooser into ``PlpCategory``."""

    model = PlpCategory
    chooser_viewset_class = PlpCategoryChooserViewSet


register_snippet(PlpCategoryViewSet)
