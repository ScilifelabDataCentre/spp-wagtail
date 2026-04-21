"""Alert block."""

from wagtail import blocks


class AlertBlock(blocks.StructBlock):
    """Alert block.

    A structured block to display styled alert messages in the CMS.

    Attributes:
        message (RichTextBlock): The content of the alert, allowing limited formatting
            options: headings (h4, h5), bold, italic, and links.
        alert_type (ChoiceBlock): The type of alert to display. Options include:
            - "info": Informational message
            - "success": Success message
            - "warning": Warning message
            - "error": Error message
            Defaults to "info". This is used for background colour of the alert.
    """

    message = blocks.RichTextBlock(
        features=["h4", "h5", "bold", "italic", "link"],
        help_text=(
            "The content of the alert, it is rich text field that supports "
            "headings (h4, h5), bold, italic, and links."
        ),
    )
    alert_type = blocks.ChoiceBlock(
        choices=[
            ("info", "Info"),
            ("success", "Success"),
            ("warning", "Warning"),
            ("error", "Error"),
        ],
        default="info",
        help_text=(
            "The type of alert to display. Selected option will determine "
            "the background colour of the alert."
        ),
    )

    class Meta:
        """Set meta values."""

        icon = "comment"
        label = "Alert"
        template = "cms/blocks/alert.html"
