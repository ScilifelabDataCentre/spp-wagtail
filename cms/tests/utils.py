"""Utility functions for testing."""

import io

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage
from wagtail.images import get_image_model


def create_test_image(*, title: str = "Test image", file_name: str = "test.jpg"):
    """Create and save a minimal test image for use in tests.

    Args:
        title (str): The title for the image.
        file_name (str): The file name for the image.

    Example usage:
        image = create_test_image(title="My Test Image", file_name="my_test_image.jpg")
    """
    file_obj = io.BytesIO()

    image = PILImage.new("RGB", (1, 1), color="white")
    image.save(file_obj, format="JPEG")

    file_obj.seek(0)

    Image = get_image_model()  # noqa: N806
    return Image.objects.create(
        title=title,
        file=SimpleUploadedFile(
            name=file_name,
            content=file_obj.read(),
            content_type="image/jpeg",
        ),
    )
