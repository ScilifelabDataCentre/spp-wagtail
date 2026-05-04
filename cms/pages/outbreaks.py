"""CMS pages for outbreaks."""

from typing import Any

from django.db import models
from django.http import HttpRequest
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.blocks import RichTextBlock
from wagtail.fields import StreamField
from wagtail.images import get_image_model_string
from wagtail.models import Page

from cms.blocks import AlertBlock, DataTableBlock

OUTBREAKS_STATUS_DEFAULT = "ongoing"
OUTBREAKS_STATUS_CHOICES = [
    ("ongoing", "Ongoing"),
    ("historical", "Historical"),
]


class OutbreaksIndexPage(Page):
    """A page listing all outbreaks.

    This page is intended to be used as a parent page for OutbreakPage instances.
    Only one instance of this page can exist. Child outbreak pages will be listed
    as cards on this page.

    Attributes:
        content (StreamField): A stream field for the page content, allowing rich text.
    """

    max_count = 1
    template = "cms/pages/outbreaks_index.html"
    parent_page_types = ["cms.HomePage"]
    subpage_types = ["cms.OutbreakPage"]

    content = StreamField(
        [
            ("text", RichTextBlock()),
            ("alert", AlertBlock()),
        ],
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("content"),
    ]

    def get_context(self, request: HttpRequest) -> dict[str, Any]:
        """Add child outbreaks to the context."""
        context = super().get_context(request)
        context["outbreaks"] = {}
        for _type, _label in OUTBREAKS_STATUS_CHOICES:
            fetched_outbreaks = (
                self.get_children()
                .type(OutbreakPage)
                .live()
                .filter(outbreakpage__status=_type)
                .specific()
                .order_by("title")
            )
            if fetched_outbreaks:
                context["outbreaks"][_type] = fetched_outbreaks
        return context


class OutbreakPage(Page):
    """A page representing a single outbreak.

    This page is intended to be used as a child of OutbreaksIndexPage. It represents
    a single outbreak and can contain content related to that outbreak.

    Attributes:
        description (str): A brief description of the outbreak.
        image (ForeignKey): An image associated with the outbreak (actually saved as a foreign key).
        status (str): The current status of the outbreak (e.g., "ongoing" or "historical").
        content (StreamField): A stream field for the page content, allowing rich text.
    """

    template = "cms/pages/outbreak.html"
    parent_page_types = ["cms.OutbreaksIndexPage"]
    subpage_types = []

    description = models.CharField(max_length=255, blank=False)
    image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=False,
        on_delete=models.PROTECT,
        related_name="+",
    )
    status = models.CharField(
        max_length=50,
        blank=False,
        choices=OUTBREAKS_STATUS_CHOICES,
        default=OUTBREAKS_STATUS_DEFAULT,
    )
    content = StreamField(
        [
            ("text", RichTextBlock()),
            ("alert", AlertBlock()),
            ("data_table", DataTableBlock()),
        ],
        blank=False,
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel(
                    "description",
                    help_text="Brief text summary that will be displayed on the outbreaks card.",
                ),
                FieldPanel(
                    "image",
                    help_text="Thumbnail image that will be displayed on the outbreaks card.",
                ),
            ],
            heading="Card details",
        ),
        FieldPanel(
            "status",
            help_text=(
                "The current status of the outbreak and will be used to "
                "group outbreaks on the index page."
            ),
        ),
        FieldPanel(
            "content",
            help_text="The main content for the outbreak page.",
        ),
    ]

    def get_context(self, request: HttpRequest) -> dict[str, Any]:
        """Add the parent page's title to the context for display on the outbreak page."""
        context = super().get_context(request)
        context["page_heading"] = self.get_parent().specific.title
        return context
