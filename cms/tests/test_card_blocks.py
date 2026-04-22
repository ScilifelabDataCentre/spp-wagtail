"""Tests for card, card grid, and child-page card StreamField blocks."""

import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image as PILImage
from wagtail.blocks import StructBlockValidationError
from wagtail.images import get_image_model
from wagtail.models import Page, Site

from cms.blocks.cards import CardBlock, CardGridBlock, ChildPageCardBlock

#######################################################################
#################### Helper functions for testing #####################
#######################################################################

Image = get_image_model()


def create_test_image(*, title: str = "Test image", file_name: str = "test.jpg"):
    """Create and save a minimal test image."""
    file_obj = io.BytesIO()

    image = PILImage.new("RGB", (1, 1), color="white")
    image.save(file_obj, format="JPEG")

    file_obj.seek(0)

    return Image.objects.create(
        title=title,
        file=SimpleUploadedFile(
            name=file_name,
            content=file_obj.read(),
            content_type="image/jpeg",
        ),
    )


#######################################################################
########################   CardBlock tests   ##########################
#######################################################################


class TestCardBlock(TestCase):
    """Tests for the CardBlock."""

    def setUp(self):
        """Set up test data."""
        self.block = CardBlock()

    def test_valid_card_data(self):
        """Test that valid data is accepted by the block."""
        image = create_test_image(title="Test image", file_name="test.jpg")
        value = self.block.to_python(
            {
                "image": image.id,
                "title": "Test title",
                "description": "Test description",
                "url": "https://example.com",
            }
        )

        result = self.block.clean(value)

        self.assertEqual(result["title"], "Test title")
        self.assertEqual(result["image"].title, "Test image")
        self.assertEqual(result["description"], "Test description")
        self.assertEqual(result["url"], "https://example.com")

    def test_missing_required_fields(self):
        """Test that missing required fields raise validation errors."""
        value = self.block.to_python({})

        with self.assertRaises(StructBlockValidationError) as ctx:
            self.block.clean(value)

        errors = ctx.exception.block_errors
        self.assertIn("image", errors)
        self.assertIn("title", errors)
        self.assertIn("description", errors)
        self.assertIn("url", errors)


#######################################################################
######################   CardGridBlock tests   ########################
#######################################################################


class TestCardGridBlock(TestCase):
    """Tests for the CardGridBlock."""

    def setUp(self):
        """Set up test data."""
        self.block = CardGridBlock()

    def test_min_num_enforced(self):
        """Test that the minimum number of cards is enforced."""
        value = self.block.to_python(
            {
                "cards": [],
            }
        )

        with self.assertRaises(StructBlockValidationError) as ctx:
            self.block.clean(value)

        errors = ctx.exception.block_errors
        self.assertIn("cards", errors)

    def test_valid_card_grid_data(self):
        """Test that valid card grid data is accepted by the block."""
        image1 = create_test_image(title="Image 1", file_name="image1.jpg")
        image2 = create_test_image(title="Image 2", file_name="image2.jpg")

        value = self.block.to_python(
            {
                "cards": [
                    {
                        "image": image1.id,
                        "title": "Card 1",
                        "description": "Description for card 1",
                        "url": "https://example.com/card1",
                    },
                    {
                        "image": image2.id,
                        "title": "Card 2",
                        "description": "Description for card 2",
                        "url": "https://example.com/card2",
                    },
                ]
            }
        )

        result = self.block.clean(value)

        self.assertEqual(len(result["cards"]), 2)
        self.assertEqual(result["cards"][0]["title"], "Card 1")
        self.assertEqual(result["cards"][0]["image"].title, "Image 1")
        self.assertEqual(result["cards"][0]["description"], "Description for card 1")
        self.assertEqual(result["cards"][0]["url"], "https://example.com/card1")
        self.assertEqual(result["cards"][1]["title"], "Card 2")
        self.assertEqual(result["cards"][1]["image"].title, "Image 2")
        self.assertEqual(result["cards"][1]["description"], "Description for card 2")
        self.assertEqual(result["cards"][1]["url"], "https://example.com/card2")


#######################################################################
####################   ChildPageCardBlock tests   #####################
#######################################################################


class TestChildPageCardBlock(TestCase):
    """Tests for the ChildPageCardBlock."""

    def setUp(self):
        """Set up test data."""

        self.root = Page.objects.get(id=1)

        Site.objects.update_or_create(
            id=1,
            defaults={
                "hostname": "localhost",
                "root_page": self.root,
                "is_default_site": True,
            },
        )

        self.parent = self.root.add_child(instance=Page(title="Parent", slug="parent"))
        self.child_b = self.parent.add_child(instance=Page(title="B page", slug="b"))  # noqa: F841
        self.child_a = self.parent.add_child(instance=Page(title="A page", slug="a"))  # noqa: F841
        self.child_d = self.parent.add_child(instance=Page(title="D page", slug="d"))  # noqa: F841
        self.child_c = self.parent.add_child(instance=Page(title="C page", slug="c"))  # noqa: F841

        self.block = ChildPageCardBlock()

    def test_returns_all_children_by_default(self):
        """Test that all child pages are returned by default."""

        value = self.block.to_python(
            {
                "parent_page": self.parent.id,
            }
        )

        result = self.block.clean(value)
        context = self.block.get_context(result)

        self.assertEqual(len(context["child_pages"]), 4)

    def test_limits_to_3(self):
        """Test that the number of child pages can be limited to 3."""
        value = self.block.to_python(
            {
                "parent_page": self.parent.id,
                "num_children": "3",
            }
        )

        result = self.block.clean(value)
        context = self.block.get_context(result)

        self.assertLessEqual(len(context["child_pages"]), 3)

    def test_order_by_title(self):
        """Test that child pages can be ordered by title."""
        value = self.block.to_python(
            {
                "parent_page": self.parent.id,
                "order_by": "title",
            }
        )

        result = self.block.clean(value)
        context = self.block.get_context(result)

        titles = [p.title for p in context["child_pages"]]
        self.assertEqual(titles, sorted(titles))

    def test_order_by_created(self):
        """Test that child pages can be ordered by creation date."""
        self.child_e = self.parent.add_child(instance=Page(title="E page", slug="e"))
        self.child_e.save_revision().publish()

        value = self.block.to_python(
            {
                "parent_page": self.parent.id,
                "order_by": "created",
            }
        )

        result = self.block.clean(value)
        context = self.block.get_context(result)

        self.assertEqual(context["child_pages"][0].title, "E page")

    def test_parent_with_no_children_returns_empty_list(self):
        """Test that a parent page with no children returns an empty list."""
        empty_parent = self.root.add_child(instance=Page(title="Empty parent", slug="empty-parent"))

        value = self.block.to_python(
            {
                "parent_page": empty_parent.id,
                "num_children": "all",
                "order_by": "created",
            }
        )

        result = self.block.clean(value)
        context = self.block.get_context(result)

        self.assertEqual(list(context["child_pages"]), [])
