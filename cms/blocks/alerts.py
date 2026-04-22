"""Alert StructBlock for styled callouts in StreamField content."""

from wagtail import blocks


class AlertBlock(blocks.StructBlock):
    """Structured block for notices, warnings, errors, or success states.

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
        help_text="Alert body. Rich text only: headings H4–H5, bold, italic, and links.",
    )
    alert_type = blocks.ChoiceBlock(
        choices=[
            ("info", "Info"),
            ("success", "Success"),
            ("warning", "Warning"),
            ("error", "Error"),
        ],
        default="info",
        help_text="Controls the visual style (colour) of the alert on the public site.",
    )

    class Meta:
        """Set meta values."""

        icon = "comment"
        label = "Alert"
        help_text = (
            "Callout for notices, warnings, or success states. Prefer short, scannable text."
        )
        template = "cms/blocks/alert.html"
