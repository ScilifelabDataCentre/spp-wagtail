"""Static figure block for SVG/PNG images."""

from typing import Any

from django.core.exceptions import ValidationError
from wagtail.blocks import CharBlock, StructBlock, URLBlock
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.images.blocks import ImageChooserBlock


class StaticFigureBlock(StructBlock):
    """Renders a static image with caption and alt text.

    Supports two image sources: an uploaded Wagtail image via the chooser,
    or an external URL (e.g., blobserver-hosted SVG). If both are provided,
    the uploaded image takes precedence.

    Attributes:
        image: Optional image from the Wagtail image library.
        image_url: Optional external URL to an image (SVG/PNG).
        caption: Optional text displayed below the image.
        alt_text: Accessibility description.
    """

    image = ImageChooserBlock(
        required=False,
        help_text="Upload an image, or leave empty and provide an external URL below.",
    )
    image_url = URLBlock(
        required=False,
        help_text=(
            "External image URL (e.g., Github, blobserver SVG). Used when no image is uploaded."
        ),
    )
    alt_text = CharBlock(
        required=True,
        help_text="Accessibility description (alt attribute) for the image.",
    )
    caption = CharBlock(
        required=False,
        help_text="Optional visible caption below the figure (separate from alt text).",
    )

    def clean(self, value: dict[str, Any]) -> dict[str, Any]:
        """Validate that at least one image source is provided."""
        cleaned = super().clean(value)
        image = cleaned.get("image")
        image_url = (cleaned.get("image_url") or "").strip()
        if not image and not image_url:
            message = "Please provide either an uploaded image or an external image URL."
            raise StructBlockValidationError(
                block_errors={
                    "image": ValidationError(message),
                    "image_url": ValidationError(message),
                },
            )
        return cleaned

    class Meta:
        """Block metadata."""

        template = "cms/blocks/static_figure.html"
        icon = "image"
        label = "Static Figure"
