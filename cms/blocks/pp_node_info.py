"""Other pathogen portal node info block."""

from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


class NodeBlock(blocks.StructBlock):
    """Node content block.

    Represents a small informational card used inside a card grid.

    Attributes:
        Country (CharBlock): Country of the node.
        flag (ImageChooserBlock): Flag of the country.
        flag (ImageChooserBlock): Logo of the node.
        description (TextBlock): Short description displayed below the title.
    """

    country = blocks.CharBlock(required=True, max_length=120)
    flag = ImageChooserBlock(required=True)
    logo = ImageChooserBlock(required=True)
    description = blocks.RichTextBlock(features=["bold", "italic", "link"])

    class Meta:
        """Set meta values."""

        icon = "placeholder"
        label = "PPN Info"
        template = "cms/blocks/pp_node.html"
