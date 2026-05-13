"""Admin form for ``PlpProjectPage`` enforcing the top-level category rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms
from wagtail.admin.forms import WagtailAdminPageForm

if TYPE_CHECKING:
    from cms.snippets.plp_category import PlpCategory


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
