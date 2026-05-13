"""CMS index page for the Pandemic Laboratory Preparedness (PLP) program."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.fields import StreamField
from wagtail.models import Page

from cms.blocks import AlertBlock, CollapsibleBlock


class PlpIndexPage(Page):
    """Landing page for the PLP program at ``/plp-program/``.

    Renders an editor-managed ``content`` StreamField (background prose, the
    timeline ``CollapsibleBlock``, and capabilities preamble) followed by
    category-grouped cards for direct ``PlpProjectPage`` children. Categories
    iterate in :class:`cms.snippets.PlpCategory` ``(order, title)`` order; cards
    inside a category preserve Wagtail child-page tree order (the admin's
    "Sort menu order" UI). Subprojects are not direct children and therefore
    never appear here.

    Attributes:
        content (StreamField): Optional rich text, alerts, and a collapsible
            block (typically holding the program timeline ``DataTableBlock``).
    """

    max_count = 1
    template = "cms/pages/plp_index.html"
    parent_page_types = ["cms.HomePage"]
    subpage_types = ["cms.PlpProjectPage"]

    content = StreamField(
        [
            ("text", RichTextBlock()),
            ("alert", AlertBlock()),
            ("collapsible", CollapsibleBlock()),
        ],
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("content"),
    ]

    def get_context(self, request: HttpRequest) -> dict[str, Any]:
        """Build ``category_groups`` for the template.

        ``category_groups`` is a list of ``{"value", "label", "projects"}``
        dicts mirroring the spp-django shape so the template can be a near
        copy. Categories are emitted in :class:`PlpCategory` ``(order, title)``
        order; the projects list inside each group keeps Wagtail child-page
        tree order. Top-level projects with ``category_id is None`` are
        silently skipped — the admin form/move gates make that state
        unreachable through the UI, so dropping them here keeps the index
        well-defined if a programmatic write ever creates one.
        """
        from cms.pages.plp_project import PlpProjectPage
        from cms.snippets.plp_category import PlpCategory

        context = super().get_context(request)

        children = self.get_children().type(PlpProjectPage).live().specific()
        projects_by_category: dict[int, list[PlpProjectPage]] = {}
        for project in children:
            if project.category_id is None:
                continue
            projects_by_category.setdefault(project.category_id, []).append(project)

        category_groups: list[dict[str, Any]] = []
        for category in PlpCategory.objects.all():
            projects = projects_by_category.get(category.pk)
            if not projects:
                continue
            category_groups.append(
                {
                    "value": category.slug,
                    "label": category.group_label,
                    "projects": projects,
                }
            )

        context["category_groups"] = category_groups
        return context
