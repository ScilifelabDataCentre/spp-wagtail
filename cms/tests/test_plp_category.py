"""Tests for the PLP category snippet."""

from django.test import TestCase

from cms.snippets import PlpCategory


class PlpCategoryModelTests(TestCase):
    """Tests for the ``PlpCategory`` snippet model."""

    def test_slug_auto_generated_from_title(self) -> None:
        """An empty slug is filled in by ``save`` based on the title."""
        category = PlpCategory.objects.create(
            title="PLP Round One",
            slug="",
            group_label="Pandemic Laboratory Preparedness Capabilities round 1",
        )

        self.assertEqual(category.slug, "plp-round-one")

    def test_slug_preserved_when_provided(self) -> None:
        """An explicit slug is not overwritten by ``save``."""
        category = PlpCategory.objects.create(
            title="PLP Round Two",
            slug="custom-plp2",
            group_label="Pandemic Laboratory Preparedness Capabilities round 2 2022",
        )

        self.assertEqual(category.slug, "custom-plp2")

    def test_default_ordering_by_order_then_title(self) -> None:
        """Default queryset ordering is ``(order, title)``."""
        plp1 = PlpCategory.objects.create(
            title="PLP1",
            slug="plp1",
            group_label="Pandemic Laboratory Preparedness Capabilities round 1",
            order=2,
        )
        tdp = PlpCategory.objects.create(
            title="TDP",
            slug="tdp",
            group_label="Technology Development Projects",
            order=1,
        )
        plp2_alpha = PlpCategory.objects.create(
            title="Alpha",
            slug="alpha",
            group_label="Alpha group",
            order=2,
        )

        ordered = list(PlpCategory.objects.all())

        self.assertEqual(ordered, [tdp, plp2_alpha, plp1])
