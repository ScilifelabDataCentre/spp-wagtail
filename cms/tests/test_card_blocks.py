"""Tests for the card blocks."""

import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image as PILImage
from wagtail.blocks import StructBlockValidationError
from wagtail.images import get_image_model

from cms.blocks.cards import CardBlock, CardGridBlock

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
