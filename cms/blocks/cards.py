"""Card related blocks."""

from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


class CardBlock(blocks.StructBlock):
    """Card content block.

    Represents a small informational card used inside a card grid.

    Attributes:
        image (ImageChooserBlock): Image displayed at the top of the card.
        title (CharBlock): Title text for the card.
        description (TextBlock): Short description displayed below the title.
    """

    image = ImageChooserBlock(required=True)
    title = blocks.CharBlock(required=True, max_length=120)
    description = blocks.TextBlock(required=True, max_length=300)
    url = blocks.URLBlock(required=True)

    class Meta:
        """Set meta values."""

        icon = "placeholder"
        label = "Card"
        template = "cms/blocks/card.html"


class CardGridBlock(blocks.StructBlock):
    """Grid container for multiple card blocks.

    Allows editors to add a list of cards that will typically be rendered
    in a grid layout on the frontend.

    Attributes:
        cards (ListBlock): Collection of CardBlock items displayed as a grid.
    """

    cards = blocks.ListBlock(CardBlock(), min_num=1, label="Cards")

    class Meta:
        """Set meta values."""

        icon = "table"
        label = "Card Grid"
        template = "cms/blocks/card_grid.html"
