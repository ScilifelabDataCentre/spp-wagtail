"""Tests for the ``SiteAnnouncement`` snippet, template tag, filter, and render.

The cases below mirror the Representative Scenarios in the plan / spec:
happy path, empty state, single-type render, toggle-off, the external-link
``rel`` merge and its edge cases, the malicious-payload non-escape,
``AlertBlock`` non-regression, and the template-tag DB-error fallback.
"""

import re
from unittest import mock

from bs4 import BeautifulSoup
from django.test import TestCase
from wagtail.admin.rich_text.converters.contentstate import ContentstateConverter
from wagtail.models import Page, Site

from cms.pages import StandardPage
from cms.snippets import SiteAnnouncement
from cms.templatetags.site_announcements import (
    announcement_rich_text,
    get_site_announcements,
)

#######################################################################
#################### Helpers for render scenarios #####################
#######################################################################


_REL_RE: re.Pattern[str] = re.compile(r'rel=[\'"]([^\'"]+)[\'"]')


def _rel_tokens_from_string(html: str) -> set[str]:
    """Return the ``rel`` tokens of the first ``<a>`` element in ``html``.

    The filter emits ``rel="token token"``; this tokeniser is used by the
    unit-level filter tests where we are only concerned with membership
    and duplication, not document order.
    """
    match = _REL_RE.search(html)
    if match is None:
        return set()
    return set(match.group(1).split())


def _editor_sanitised(raw_html: str) -> str:
    """Simulate the Wagtail admin's Draftail sanitisation round-trip.

    When an editor saves a ``RichTextField`` via the admin, the submitted
    HTML is converted to Draftail's ContentState and back, which drops
    elements outside the configured feature set. Tests creating rows via
    ``SiteAnnouncement.objects.create`` bypass the widget, so this helper
    applies the same transformation programmatically.

    Args:
        raw_html (str): HTML a malicious editor might try to paste.

    Returns:
        str: HTML after the ``bold`` / ``italic`` / ``link`` round-trip.
    """
    converter = ContentstateConverter(["bold", "italic", "link"])
    return converter.to_database_format(converter.from_database_format(raw_html))


class _SiteAnnouncementRenderTestCase(TestCase):
    """Base class that sets up a Wagtail site with a renderable page tree.

    The default Wagtail migration tree already installs a root (id=1)
    and a ``home`` page (id=2) bound to the default ``Site``. We reuse
    that home page as the parent so the site's ``root_page`` resolves
    without recreating a fixture, and add ``StandardPage`` children for
    the actual render assertions.
    """

    def setUp(self) -> None:
        """Reuse the default Wagtail home page and add a blank ``StandardPage`` child."""
        self.site = Site.objects.get(is_default_site=True)
        self.home = self.site.root_page
        self.standard_page = self.home.add_child(
            instance=StandardPage(title="Standard", slug="standard", content=[]),
        )

    def _render(self, page: Page | None = None) -> str:
        """Request ``page`` (defaults to ``self.standard_page``) and return the body."""
        target = page or self.standard_page
        response = self.client.get(target.url)
        self.assertEqual(response.status_code, 200)
        return response.content.decode()


#######################################################################
######################### Model-level sanity ##########################
#######################################################################


class SiteAnnouncementModelTests(TestCase):
    """Basic model guarantees: verbose name, ``__str__``, default ordering."""

    def test_verbose_name_is_site_announcement(self):
        """The Meta ``verbose_name`` drives the Wagtail admin sidebar label."""
        self.assertEqual(SiteAnnouncement._meta.verbose_name, "Site announcement")

    def test_str_returns_title(self):
        """``__str__`` returns the title for admin list views."""
        announcement = SiteAnnouncement.objects.create(
            title="Down for maintenance",
            message="<p>hello</p>",
            announcement_type="maintenance",
        )
        self.assertEqual(str(announcement), "Down for maintenance")

    def test_default_queryset_ordering_by_sort_order(self):
        """``Meta.ordering = ['sort_order', 'pk']`` gives deterministic order."""
        SiteAnnouncement.objects.create(
            title="B",
            message="<p>x</p>",
            announcement_type="survey",
            sort_order=2,
        )
        SiteAnnouncement.objects.create(
            title="A",
            message="<p>x</p>",
            announcement_type="survey",
            sort_order=1,
        )
        titles = list(SiteAnnouncement.objects.values_list("title", flat=True))
        self.assertEqual(titles, ["A", "B"])


#######################################################################
################ announcement_rich_text filter (unit) #################
#######################################################################


class AnnouncementRichTextFilterTests(TestCase):
    """Filter behaviour covering every anchor-scope branch.

    These tests call ``announcement_rich_text`` directly — no page, no
    template — so the assertions target the filter's rel-merge
    contract without relying on Wagtail's rendering pipeline.
    """

    def test_external_https_anchor_gets_required_rel_tokens(self):
        """``https://`` anchor without ``rel`` gets ``noopener`` + ``noreferrer``."""
        rendered = announcement_rich_text('<p><a href="https://example.com">link</a></p>')
        self.assertEqual(_rel_tokens_from_string(rendered), {"noopener", "noreferrer"})

    def test_external_http_anchor_also_rewritten(self):
        """``http://`` anchors are treated as external for ``rel`` injection."""
        rendered = announcement_rich_text('<p><a href="http://example.com">link</a></p>')
        self.assertTrue(
            {"noopener", "noreferrer"}.issubset(_rel_tokens_from_string(rendered)),
        )

    def test_protocol_relative_anchor_treated_as_external(self):
        """Protocol-relative ``//host/…`` is external (SEO / tabnabbing surface)."""
        rendered = announcement_rich_text('<p><a href="//host.example/path">link</a></p>')
        self.assertTrue(
            {"noopener", "noreferrer"}.issubset(_rel_tokens_from_string(rendered)),
        )

    def test_editor_rel_nofollow_preserved_and_deduped(self):
        """Editor's ``nofollow`` is preserved; final set is the three tokens."""
        rendered = announcement_rich_text(
            '<p><a href="https://partner.example" rel="nofollow">link</a></p>',
        )
        self.assertEqual(
            _rel_tokens_from_string(rendered),
            {"nofollow", "noopener", "noreferrer"},
        )

    def test_existing_noopener_not_duplicated(self):
        """An existing ``noopener`` token is not duplicated by the merge."""
        rendered = announcement_rich_text(
            '<p><a href="https://example.com" rel="noopener">link</a></p>',
        )
        self.assertEqual(_rel_tokens_from_string(rendered), {"noopener", "noreferrer"})

    def test_external_anchor_gets_target_blank(self):
        """External anchors are forced to ``target="_blank"`` (open in new tab)."""
        rendered = announcement_rich_text('<p><a href="https://example.com">link</a></p>')
        self.assertIn('target="_blank"', rendered)

    def test_relative_anchor_does_not_get_target_blank(self):
        """Same-origin anchors are not given ``target="_blank"``."""
        rendered = announcement_rich_text('<p><a href="/about">about</a></p>')
        self.assertNotIn("target=", rendered)

    def test_mailto_href_left_untouched(self):
        """``mailto:`` anchors are not whitelisted by the filter."""
        rendered = announcement_rich_text('<p><a href="mailto:x@example.com">email</a></p>')
        self.assertNotIn("noopener", rendered)
        self.assertNotIn("noreferrer", rendered)

    def test_relative_path_anchor_left_untouched(self):
        """A relative path is same-origin; the filter does not touch it."""
        rendered = announcement_rich_text('<p><a href="/about">about</a></p>')
        self.assertNotIn("noopener", rendered)
        self.assertNotIn("noreferrer", rendered)

    def test_fragment_anchor_left_untouched(self):
        """Fragment-only hrefs are not rewritten."""
        rendered = announcement_rich_text('<p><a href="#section">section</a></p>')
        self.assertNotIn("noopener", rendered)
        self.assertNotIn("noreferrer", rendered)

    def test_javascript_href_left_untouched(self):
        """``javascript:`` must never be whitelisted by this filter."""
        rendered = announcement_rich_text('<p><a href="javascript:alert(1)">x</a></p>')
        self.assertNotIn("noopener", rendered)
        self.assertNotIn("noreferrer", rendered)

    def test_data_href_left_untouched(self):
        """``data:`` URIs must never be whitelisted by this filter."""
        rendered = announcement_rich_text('<p><a href="data:text/html,x">x</a></p>')
        self.assertNotIn("noopener", rendered)
        self.assertNotIn("noreferrer", rendered)


#######################################################################
############### get_site_announcements template tag ###################
#######################################################################


class GetSiteAnnouncementsTemplateTagTests(TestCase):
    """Tests for the ``get_site_announcements`` simple_tag."""

    def test_returns_only_enabled_rows_in_sort_order(self):
        """Disabled rows are filtered out; enabled rows are ordered by ``sort_order``."""
        SiteAnnouncement.objects.create(
            title="hidden",
            message="<p>x</p>",
            announcement_type="maintenance",
            is_enabled=False,
            sort_order=0,
        )
        SiteAnnouncement.objects.create(
            title="second",
            message="<p>x</p>",
            announcement_type="survey",
            is_enabled=True,
            sort_order=2,
        )
        SiteAnnouncement.objects.create(
            title="first",
            message="<p>x</p>",
            announcement_type="maintenance",
            is_enabled=True,
            sort_order=1,
        )

        titles = [a.title for a in get_site_announcements()]

        self.assertEqual(titles, ["first", "second"])

    def test_returns_empty_iterable_on_database_exception(self):
        """Broad DB/ORM exception path returns ``SiteAnnouncement.objects.none()``."""
        with mock.patch("cms.templatetags.site_announcements.SiteAnnouncement") as mocked:
            mocked.objects.filter.side_effect = Exception("db exploded")
            mocked.objects.none.return_value = []

            result = get_site_announcements()

        self.assertEqual(list(result), [])
        mocked.objects.none.assert_called_once()


#######################################################################
##################### End-to-end render behaviour #####################
#######################################################################


class SiteAnnouncementRenderTests(_SiteAnnouncementRenderTestCase):
    """Full render tests: the announcement region surfaces in public pages."""

    def test_happy_path_two_banners_sorted_with_correct_class_map(self):
        """Two enabled banners render in ``sort_order`` with the correct class map.

        Also: one single outer ``<section aria-label="Site announcements">``,
        no ``role="alert"`` on any descendant, no ``aria-live`` attribute.
        """
        SiteAnnouncement.objects.create(
            title="Maintenance one",
            message="<p>Maintenance banner copy</p>",
            announcement_type="maintenance",
            is_enabled=True,
            sort_order=1,
        )
        SiteAnnouncement.objects.create(
            title="Survey one",
            message="<p>Survey banner copy</p>",
            announcement_type="survey",
            is_enabled=True,
            sort_order=2,
        )

        html = self._render()
        soup = BeautifulSoup(html, "html.parser")

        sections = soup.find_all("section", attrs={"aria-label": "Site announcements"})
        self.assertEqual(len(sections), 1)
        section = sections[0]
        self.assertIsNone(section.get("role"))
        self.assertIsNone(section.get("aria-live"))
        self.assertIsNone(section.find(attrs={"role": "alert"}))
        self.assertIsNone(section.find(attrs={"aria-live": True}))

        banners = section.find_all("div", class_="alert")
        banner_classes = [" ".join(b.get("class", [])) for b in banners]
        self.assertEqual(banner_classes, ["alert alert-warning", "alert alert-info"])

    def test_empty_state_renders_no_announcement_section(self):
        """Zero enabled rows → ``<section aria-label>`` absent from the response."""
        SiteAnnouncement.objects.create(
            title="hidden",
            message="<p>hidden body</p>",
            announcement_type="maintenance",
            is_enabled=False,
        )

        html = self._render()

        self.assertNotIn("Site announcements", html)

    def test_single_type_render_shows_only_alert_info(self):
        """Only a survey is enabled → ``alert-info`` present, ``alert-warning`` absent."""
        SiteAnnouncement.objects.create(
            title="just a survey",
            message="<p>Please respond</p>",
            announcement_type="survey",
            is_enabled=True,
        )

        html = self._render()

        self.assertIn('class="alert alert-info"', html)
        self.assertNotIn("alert-warning", html)

    def test_toggle_off_removes_banner_from_subsequent_response(self):
        """Setting ``is_enabled=False`` makes the banner disappear from public pages."""
        banner = SiteAnnouncement.objects.create(
            title="toggle me",
            message="<p>toggle-banner-marker</p>",
            announcement_type="maintenance",
            is_enabled=True,
        )
        self.assertIn("toggle-banner-marker", self._render())

        banner.is_enabled = False
        banner.save()

        html = self._render()
        self.assertNotIn("toggle-banner-marker", html)
        self.assertNotIn("Site announcements", html)

    def test_external_anchor_in_announcement_gets_rel_tokens(self):
        """An announcement's external anchor renders with ``noopener`` + ``noreferrer``."""
        SiteAnnouncement.objects.create(
            title="ext",
            message='<p>See <a href="https://status.example/page">status</a></p>',
            announcement_type="maintenance",
            is_enabled=True,
        )

        soup = BeautifulSoup(self._render(), "html.parser")

        anchor = soup.find("a", href="https://status.example/page")
        self.assertIsNotNone(anchor)
        self.assertTrue(
            {"noopener", "noreferrer"}.issubset(set(anchor.get("rel") or [])),
        )

    def test_external_anchor_in_announcement_opens_in_new_tab(self):
        """An announcement's external anchor renders with ``target="_blank"``."""
        SiteAnnouncement.objects.create(
            title="ext",
            message='<p>See <a href="https://status.example/">status</a></p>',
            announcement_type="maintenance",
            is_enabled=True,
        )

        soup = BeautifulSoup(self._render(), "html.parser")

        anchor = soup.find("a", href="https://status.example/")
        self.assertIsNotNone(anchor)
        self.assertEqual(anchor.get("target"), "_blank")

    def test_editor_rel_nofollow_preserved_in_response(self):
        """Editor ``rel="nofollow"`` survives the merge in the rendered response."""
        SiteAnnouncement.objects.create(
            title="partner",
            message=('<p><a href="https://partner.example" rel="nofollow">partner link</a></p>'),
            announcement_type="maintenance",
            is_enabled=True,
        )

        soup = BeautifulSoup(self._render(), "html.parser")

        anchor = soup.find("a", href="https://partner.example")
        self.assertIsNotNone(anchor)
        self.assertEqual(
            set(anchor.get("rel") or []),
            {"nofollow", "noopener", "noreferrer"},
        )

    def test_alert_block_anchor_is_not_rewritten_by_announcement_filter(self):
        """``announcement_rich_text`` must not touch anchors inside ``AlertBlock``.

        The filter is per-banner only; applying it globally would mutate
        anchors in unrelated StreamField content such as ``AlertBlock``.
        We verify the filter-scope by rendering a page that contains
        both an announcement anchor *and* an ``AlertBlock`` anchor: the
        former gets ``rel`` injected, the latter is byte-identical to
        what the block template emits.
        """
        page_with_alert = self.home.add_child(
            instance=StandardPage(
                title="With alert",
                slug="with-alert",
                content=[
                    (
                        "alert",
                        {
                            "message": (
                                '<p><a href="https://alertblock.example">alert link</a></p>'
                            ),
                            "alert_type": "info",
                        },
                    ),
                ],
            ),
        )
        SiteAnnouncement.objects.create(
            title="banner",
            message=('<p><a href="https://announcement.example">banner link</a></p>'),
            announcement_type="survey",
            is_enabled=True,
        )

        soup = BeautifulSoup(self._render(page_with_alert), "html.parser")

        announcement_anchor = soup.find("a", href="https://announcement.example")
        self.assertIsNotNone(announcement_anchor)
        self.assertTrue(
            {"noopener", "noreferrer"}.issubset(
                set(announcement_anchor.get("rel") or []),
            ),
        )

        alert_anchor = soup.find("a", href="https://alertblock.example")
        self.assertIsNotNone(alert_anchor)
        self.assertFalse(alert_anchor.has_attr("rel"))

    def test_malicious_payload_is_absent_from_rendered_response(self):
        """Attacker payloads survive neither save nor render.

        Wagtail's Draftail round-trip (``features=[bold, italic, link]``)
        strips ``<script>`` elements and disallowed anchor schemes on
        save; the ``announcement_rich_text`` filter leaves the cleaned
        output alone rather than re-introducing them. We assert that
        ``javascript:``, ``data:text/html``, and ``<script>alert`` are
        all absent from the rendered response.
        """
        dirty = (
            '<p><a href="javascript:alert(1)">x</a>'
            '<a href="data:text/html,x">y</a>'
            "<script>alert(1)</script></p>"
        )
        clean_message = _editor_sanitised(dirty)
        self.assertNotIn("javascript:", clean_message)
        self.assertNotIn("data:text/html", clean_message)
        self.assertNotIn("<script>", clean_message)

        SiteAnnouncement.objects.create(
            title="evil",
            message=clean_message,
            announcement_type="maintenance",
            is_enabled=True,
        )

        html = self._render()

        self.assertNotIn("javascript:", html)
        self.assertNotIn("data:text/html", html)
        self.assertNotIn("<script>alert", html)
