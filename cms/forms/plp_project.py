"""Admin forms for ``PlpProjectPage`` (edit and copy)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django import forms
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.forms.pages import CopyForm

if TYPE_CHECKING:
    from cms.snippets.plp_category import PlpCategory


class PlpProjectPageCopyForm(CopyForm):
    """Blocks copy operations that would break PLP depth-1 or top-level category rules."""

    def clean(self) -> dict[str, Any]:
        """Apply Wagtail copy validation plus PLP nesting and category rules."""
        cleaned_data = super().clean()

        parent_page = cleaned_data.get("new_parent_page") or self.page.get_parent()
        if parent_page is None:
            return cleaned_data

        from cms.pages.plp_index import PlpIndexPage
        from cms.pages.plp_project import PlpProjectPage

        parent_specific = parent_page.specific
        source_specific = self.page.specific

        if cleaned_data.get("copy_subpages") and isinstance(parent_specific, PlpProjectPage):
            self.add_error(
                "copy_subpages",
                forms.ValidationError(
                    "Copying subpages under another PLP project is not allowed "
                    "(would exceed the maximum nesting depth).",
                ),
            )

        if isinstance(parent_specific, PlpProjectPage) and isinstance(
            parent_specific.get_parent().specific, PlpProjectPage
        ):
            self.add_error(
                "new_parent_page",
                forms.ValidationError(
                    "Copying a project under a subproject is not allowed "
                    "(would exceed the maximum nesting depth).",
                ),
            )

        if (
            isinstance(parent_specific, PlpIndexPage)
            and isinstance(source_specific, PlpProjectPage)
            and source_specific.category_id is None
        ):
            self.add_error(
                "new_parent_page",
                forms.ValidationError(
                    "A category is required when copying to the PLP overview; "
                    "set one on the source page first.",
                ),
            )

        return cleaned_data


class PlpProjectPageForm(WagtailAdminPageForm):
    """Validates that ``category`` is supplied when the parent is a ``PlpIndexPage``.

    Wagtail's create view (`wagtail/admin/views/pages/create.py:163-170`) and edit
    view (`wagtail/admin/views/pages/edit.py:464-469`) both inject the prospective
    parent into the form as ``parent_page`` before ``add_child()`` runs. We rely
    on that attribute rather than ``self.instance.get_parent()``, which is unsafe
    on the create path because Treebeard's ``_cached_parent_obj`` is unset until
    the page is saved into the tree.

    The model field stays ``null=True, blank=True`` so subprojects (whose parent
    is itself a ``PlpProjectPage``) can save without a category.
    """

    def clean_category(self) -> PlpCategory | None:
        """Reject an empty ``category`` only when the parent is a ``PlpIndexPage``."""
        from cms.pages.plp_index import PlpIndexPage

        category = self.cleaned_data.get("category")
        parent_specific = self.parent_page.specific if self.parent_page else None
        is_top_level = isinstance(parent_specific, PlpIndexPage)
        if is_top_level and not category:
            raise forms.ValidationError("This field is required for top-level projects.")
        return category
