"""Card related blocks."""

from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


class CardBlock(blocks.StructBlock):
    """Card content block.

    Represents a small informational card used inside a card grid. Can also be
    used on its own if needed.

    Attributes:
        image (ImageChooserBlock): Image displayed at the top of the card.
        title (CharBlock): Title text for the card.
        description (TextBlock): Short description displayed below the title.
        url (URLBlock): URL the card links to when clicked (opens in new tab).
    """

    # TODO: Depending on the design, we might want to add more optional fields
    # here like a date, topic, etc.

    image = ImageChooserBlock(required=True)
    title = blocks.CharBlock(required=True, max_length=120)
    description = blocks.TextBlock(required=True, max_length=300)
    url = blocks.URLBlock(required=True)

    class Meta:
        """Set meta values."""

        icon = "placeholder"
        label = "Card"
        collapsed = True
        template = "cms/blocks/card.html"


class CardGridBlock(blocks.StructBlock):
    """Grid container for multiple card blocks.

    Allows editors to add a list of cards manually that will typically be rendered
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
