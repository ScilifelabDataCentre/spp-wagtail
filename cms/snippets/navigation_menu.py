"""Navigation menu snippet."""

from django.db import models
from django.utils.text import slugify
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import (
    FieldPanel,
    InlinePanel,
    PageChooserPanel,
)
from wagtail.models import Orderable
from wagtail.snippets.models import register_snippet


class NavigationMenuForm(WagtailAdminModelForm):
    """Custom admin form for validating navigation menu structure.

    This form ensures that main menu items and submenu items are
    are added as expected.
    """

    def clean(self) -> None:
        """Extend default validation with custom validation rules.

        Validation rules:
            - If a main menu item does not have `has_submenu` enabled,
              it must include a top-level page reference and must not
              contain any sub menu items.
            - If a main menu item has `has_submenu` enabled,
              it must not include a top-level page reference and
              must contain at least one sub menu item.
            - For footer menu, main menu items must not have sub menu items,
              they must only have top-level page reference.
            - Each sub menu item must include a valid page reference.
        """
        super().clean()

        if "main_menu_items" in self.formsets:
            for form in self.formsets["main_menu_items"].forms:
                if form.is_valid() and not form.cleaned_data.get("DELETE", False):
                    if form.cleaned_data.get("has_submenu"):
                        # when has_submenu is True, check that page is not set
                        if form.cleaned_data.get("page"):
                            form.add_error(
                                "page", "Top-level page not needed if it has sub menu items."
                            )
                        # when has_submenu is True, check that at least one sub menu item is added
                        if len(form.formsets.get("sub_menu_items", [])) == 0:
                            form.add_error(
                                "has_submenu",
                                "If this is checked, minimum one submenu item must be added below.",
                            )
                        else:
                            # has_submenu should not be enabled for footer menu items
                            if self.cleaned_data.get("slug") == "footer":
                                form.add_error(
                                    "has_submenu",
                                    (
                                        "Footer menu items must not have sub menu items, uncheck "
                                        "the box, remove the sub menu items and add top-level "
                                        "page reference instead."
                                    ),
                                )
                            # when has_submenu is True, check that each sub menu item has a page ref
                            else:
                                for sub_form in form.formsets["sub_menu_items"].forms:
                                    if sub_form.is_valid() and not sub_form.cleaned_data.get(
                                        "page"
                                    ):
                                        sub_form.add_error(
                                            "page",
                                            "Sub menu item must have an internal page selected.",
                                        )
                    # when has_submenu is False, check that top-level page is set
                    elif not form.cleaned_data.get("page"):
                        form.add_error(
                            "page",
                            "Menu item must have an internal page if it don't have sub menu items.",
                        )
                    # when has_submenu is False, check that no sub menu items are added
                    elif len(form.formsets.get("sub_menu_items", [])) != 0:
                        form.add_error(
                            "has_submenu",
                            "Submenu item must not be added below without checking the box.",
                        )


@register_snippet
class NavigationMenu(ClusterableModel):
    """A navigation menu snippet.

    This snippet represents a full menu, e.g., a header or footer menu,
    and can contain any number of main menu items, each optionally having
    sub-menu items. Slugs are auto-generated from the title if not provided,
    but can be edited manually.

    Attributes:
        title (str): The display title of the navigation menu.
        slug (str): Unique identifier for the menu, typically used in templates
            to fetch the menu.
        main_menu_items (RelatedManager): Reverse relation to associated
            main menu items.
    """

    title = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    panels = [
        FieldPanel("title", help_text="Title of the navigation menu."),
        FieldPanel(
            "slug",
            help_text=(
                "Unique identifier for the menu in slug format. For header menu, use 'header' and "
                "for footer menu, use 'footer'. Otherwise, template tag would not find the header "
                "and footer menu."
            ),
        ),
        # Use NavigationMainMenu model in inline panel
        InlinePanel("main_menu_items", label="Menu items"),
    ]
    base_form_class = NavigationMenuForm

    def save(self, *args, **kwargs) -> None:
        """Auto-generate slug from title if not provided."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return a human-readable representation."""
        return self.title

    class Meta:
        """Settings for the navigation menu snippet."""

        verbose_name = "Navigation menu"
        verbose_name_plural = "Navigation menu"


####################################################################################
############                    Helper Menu Item models                 ############
####################################################################################


class MenuItem(Orderable):
    """An abstract Menu item class.

    This class provides the shared fields and behaviour for both main menu
    and sub-menu items. It is not meant to be used directly, but inherited
    by concrete menu models.

    Attributes:
        title (str): The display title of the menu item.
        page (wagtailcore.Page): Optional Wagtail page linked to this item.
            If None, `link` returns '#'.
    """

    title = models.CharField(max_length=50)
    page = models.ForeignKey(
        "wagtailcore.Page",
        blank=True,
        null=True,
        related_name="+",
        on_delete=models.SET_NULL,
    )

    panels = [
        FieldPanel("title"),
        PageChooserPanel("page"),
    ]

    class Meta:
        """Settings for the abstract base menu item."""

        abstract = True

    @property
    def link(self) -> str:
        """Get URL of the menu item."""
        return self.page.url if self.page else "#"

    def __str__(self) -> str:
        """Return a human-readable representation."""
        return self.title


class NavigationMainMenu(MenuItem, ClusterableModel):
    """A main menu item in a navigation menu.

    Main menu items can either link directly to a page or serve as a container
    for sub-menu items. Validation ensures that sub menu items do not have a
    top-level page and that non-submenu items must have a page.

    Attributes:
        parent (NavigationMenu): The parent NavigationMenu instance this item belongs to.
        has_submenu (bool): True if this item has sub-menu items; otherwise False.
        sub_menu_items (RelatedManager): Reverse relation to associated sub-menu items.
    """

    # Creates the reference to NavigationMenu snippet
    parent = ParentalKey(
        "cms.NavigationMenu",
        related_name="main_menu_items",
        on_delete=models.CASCADE,
    )

    has_submenu = models.BooleanField(default=False, blank=True)

    panels = MenuItem.panels + [
        FieldPanel(
            "has_submenu",
            help_text=(
                "Enable to add sub menu items, otherwise it will fail during validation. "
                "For footer menu items, sub menu items are not allowed."
            ),
        ),
        # Use NavigationSubMenu model in inline panel
        InlinePanel("sub_menu_items", label="Sub menu items"),
    ]

    class Meta:
        """Settings for main menu items."""

        ordering = ["sort_order"]
        verbose_name = "Menu item"
        verbose_name_plural = "Menu items"


class NavigationSubMenu(MenuItem):
    """A sub-menu item that belongs to a main menu item.

    Sub-menu items must always link to a page. They cannot exist independently
    and must have a parent main menu item.

    Attributes:
        parent_menu (NavigationMainMenu): The main menu item that this sub-menu belongs to.
    """

    # Creates the reference to NavigationMainMenu model
    parent_menu = ParentalKey(
        "cms.NavigationMainMenu",
        related_name="sub_menu_items",
        on_delete=models.CASCADE,
    )

    class Meta:
        """Settings for sub-menu items."""

        ordering = ["sort_order"]
        verbose_name = "Sub menu item"
        verbose_name_plural = "Sub menu items"
