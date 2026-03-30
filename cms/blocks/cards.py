"""Card related blocks."""

from typing import Any

from django import forms
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


class ChildPageCardBlock(blocks.StructBlock):
    """Child page cards block.

    A block to display child pages of a selected parent page as cards with options
    for limiting number of items and ordering.

    Attributes:
        parent_page (PageChooserBlock): Parent page to pull child pages from.
        num_children (ChoiceBlock): How many child pages to display ("all" or "3").
        order_by (ChoiceBlock): Field to order child pages by ("latest" or "title").
    """

    # TODO: After the page models are implemented, this block either needs to be updated or
    # the block's template need to be updated to include more information like date, topic, etc.
    #
    # Depending on the need, a new block based on this one could be created to cover additional
    # use cases. For example, a block that allows selecting specific pages instead of pulling all
    # children from a parent page. We can discuss then and decide to either update this block
    # or create a new ones.
    #
    # For now, this block is a placeholder to demonstrate how to pull child pages and display
    # them as cards easily.

    parent_page = blocks.PageChooserBlock()
    num_children = blocks.ChoiceBlock(
        choices=[
            ("all", "All"),
            ("3", "3"),
        ],
        default="all",
        label="Number of child pages",
        widget=forms.RadioSelect,
    )
    order_by = blocks.ChoiceBlock(
        choices=[
            ("created", "Created date (newest first)"),
            ("updated", "Updated date (newest first)"),
            ("title", "Title (A-Z)"),
        ],
        default="created",
        label="Order by",
        widget=forms.RadioSelect,
    )

    def get_context(
        self, value: dict[str, Any], parent_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Compute child pages based on selected parent, limit, and ordering."""

        context = super().get_context(value, parent_context)
        parent = value.get("parent_page")

        if parent:
            pages = parent.get_children().live().specific()

            # Order pages
            if value.get("order_by") == "created":
                pages = pages.order_by("-first_published_at")
            elif value.get("order_by") == "updated":
                pages = pages.order_by("-last_published_at")
            elif value.get("order_by") == "title":
                pages = pages.order_by("title")

            # Limit number of pages
            if value.get("num_children") == "3":
                pages = pages[:3]

            context["child_pages"] = pages
        else:
            context["child_pages"] = []

        return context

    class Meta:
        """Set meta values."""

        icon = "form"
        label = "Child Page Cards"
        template = "cms/blocks/card_child_pages.html"
