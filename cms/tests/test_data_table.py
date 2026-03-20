"""Tests for the DataTableBlock feature: service, block, and view layers."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from wagtail.models import Page, PageViewRestriction

from cms.blocks import DataTableBlock
from cms.pages import HomePage, StandardPage
from cms.services.data_table import extract_table_data, get_table_context


def _make_typed_table(
    headers: list[str],
    rows: list[list[Any]],
) -> SimpleNamespace:
    """Build a lightweight stand-in for a ``TypedTable`` bound value."""
    return SimpleNamespace(
        columns=[{"heading": h} for h in headers],
        row_data=[{"values": vals} for vals in rows],
    )


# ---------------------------------------------------------------------------
# Service layer: extract_table_data
# ---------------------------------------------------------------------------


class ExtractTableDataTest(SimpleTestCase):
    """Unit tests for ``extract_table_data``."""

    def test_none_returns_empty(self) -> None:
        headers, rows = extract_table_data(None)
        self.assertEqual(headers, [])
        self.assertEqual(rows, [])

    def test_empty_columns_returns_empty(self) -> None:
        table = SimpleNamespace(columns=[], row_data=[])
        headers, rows = extract_table_data(table)
        self.assertEqual(headers, [])
        self.assertEqual(rows, [])

    def test_extracts_headers_and_rows(self) -> None:
        table = _make_typed_table(
            ["Name", "Score"],
            [["Alice", 95], ["Bob", 87]],
        )
        headers, rows = extract_table_data(table)
        self.assertEqual(headers, ["Name", "Score"])
        self.assertEqual(rows, [["Alice", 95], ["Bob", 87]])

    def test_preserves_rich_text_values(self) -> None:
        """RichTextValue-like objects must pass through untouched."""

        class _FakeRichText:
            def __html__(self) -> str:
                return "<b>bold</b>"

        rich = _FakeRichText()
        table = _make_typed_table(["Content"], [[rich]])
        _, rows = extract_table_data(table)
        self.assertIs(rows[0][0], rich)


# ---------------------------------------------------------------------------
# Service layer: get_table_context
# ---------------------------------------------------------------------------


class GetTableContextTest(SimpleTestCase):
    """Unit tests for ``get_table_context``."""

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.headers = ["Name", "Value"]
        self.rows: list[list[Any]] = [[f"item-{i}", i] for i in range(30)]

    def test_returns_all_expected_keys(self) -> None:
        ctx = get_table_context(
            request=None,
            rows=self.rows,
            headers=self.headers,
            table_url="/test/",
            table_id="tbl",
        )
        expected_keys = {
            "table_id",
            "table_label",
            "table_url",
            "headers",
            "page_obj",
            "page_range",
            "search",
            "per_page",
            "per_page_options",
            "total_count",
            "start_index",
            "end_index",
            "show_controls",
        }
        self.assertEqual(set(ctx.keys()), expected_keys)

    def test_none_request_uses_defaults(self) -> None:
        ctx = get_table_context(
            request=None,
            rows=self.rows,
            headers=self.headers,
            table_url="/test/",
        )
        self.assertEqual(ctx["search"], "")
        self.assertEqual(ctx["per_page"], 10)
        self.assertEqual(ctx["total_count"], 30)

    def test_label_falls_back_to_table_id(self) -> None:
        ctx = get_table_context(
            request=None,
            rows=[],
            headers=[],
            table_url="/t/",
            table_id="my-table",
            table_label="",
        )
        self.assertEqual(ctx["table_label"], "my-table")

    def test_explicit_label_used(self) -> None:
        ctx = get_table_context(
            request=None,
            rows=[],
            headers=[],
            table_url="/t/",
            table_id="my-table",
            table_label="My Table",
        )
        self.assertEqual(ctx["table_label"], "My Table")

    def test_search_filters_rows(self) -> None:
        request = self.factory.get("/", {"search": "item-5"})
        ctx = get_table_context(
            request=request,
            rows=self.rows,
            headers=self.headers,
            table_url="/test/",
        )
        self.assertEqual(ctx["total_count"], 1)
        self.assertEqual(list(ctx["page_obj"])[0], ["item-5", 5])

    def test_search_strips_html_tags(self) -> None:
        rows: list[list[Any]] = [["<b>Alpha</b>", 1], ["Beta", 2]]
        request = self.factory.get("/", {"search": "alpha"})
        ctx = get_table_context(
            request=request,
            rows=rows,
            headers=["Name", "Val"],
            table_url="/test/",
        )
        self.assertEqual(ctx["total_count"], 1)

    def test_search_is_case_insensitive(self) -> None:
        request = self.factory.get("/", {"search": "ITEM-0"})
        ctx = get_table_context(
            request=request,
            rows=self.rows,
            headers=self.headers,
            table_url="/test/",
        )
        self.assertEqual(ctx["total_count"], 1)

    def test_invalid_per_page_falls_back_to_default(self) -> None:
        request = self.factory.get("/", {"per_page": "999"})
        ctx = get_table_context(
            request=request,
            rows=self.rows,
            headers=self.headers,
            table_url="/test/",
            per_page_default=10,
        )
        self.assertEqual(ctx["per_page"], 10)

    def test_non_numeric_per_page_falls_back(self) -> None:
        request = self.factory.get("/", {"per_page": "abc"})
        ctx = get_table_context(
            request=request,
            rows=self.rows,
            headers=self.headers,
            table_url="/test/",
        )
        self.assertEqual(ctx["per_page"], 10)

    def test_pagination_defaults_to_page_one(self) -> None:
        ctx = get_table_context(
            request=None,
            rows=self.rows,
            headers=self.headers,
            table_url="/test/",
            per_page_default=10,
        )
        self.assertEqual(ctx["page_obj"].number, 1)
        self.assertEqual(ctx["start_index"], 1)
        self.assertEqual(ctx["end_index"], 10)

    def test_explicit_page_number(self) -> None:
        request = self.factory.get("/", {"page": "2"})
        ctx = get_table_context(
            request=request,
            rows=self.rows,
            headers=self.headers,
            table_url="/test/",
            per_page_default=10,
        )
        self.assertEqual(ctx["page_obj"].number, 2)
        self.assertEqual(ctx["start_index"], 11)

    def test_invalid_page_number_defaults_to_first(self) -> None:
        request = self.factory.get("/", {"page": "xyz"})
        ctx = get_table_context(
            request=request,
            rows=self.rows,
            headers=self.headers,
            table_url="/test/",
        )
        self.assertEqual(ctx["page_obj"].number, 1)

    def test_out_of_range_page_returns_last(self) -> None:
        request = self.factory.get("/", {"page": "999"})
        ctx = get_table_context(
            request=request,
            rows=self.rows,
            headers=self.headers,
            table_url="/test/",
            per_page_default=10,
        )
        self.assertEqual(ctx["page_obj"].number, 3)

    def test_show_controls_passed_through(self) -> None:
        ctx = get_table_context(
            request=None,
            rows=[],
            headers=[],
            table_url="/t/",
            show_controls=False,
        )
        self.assertFalse(ctx["show_controls"])

    def test_show_controls_false_disables_pagination(self) -> None:
        """All rows appear on a single page when controls are hidden."""
        ctx = get_table_context(
            request=None,
            rows=self.rows,
            headers=self.headers,
            table_url="/test/",
            per_page_default=10,
            show_controls=False,
        )
        self.assertEqual(ctx["total_count"], 30)
        self.assertEqual(len(list(ctx["page_obj"])), 30)
        self.assertEqual(ctx["page_obj"].paginator.num_pages, 1)

    def test_empty_rows_returns_zero_counts(self) -> None:
        ctx = get_table_context(
            request=None,
            rows=[],
            headers=[],
            table_url="/t/",
        )
        self.assertEqual(ctx["total_count"], 0)
        self.assertEqual(ctx["start_index"], 0)
        self.assertEqual(ctx["end_index"], 0)


# ---------------------------------------------------------------------------
# Block layer: DataTableBlock.get_context
# ---------------------------------------------------------------------------


class DataTableBlockContextTest(SimpleTestCase):
    """Tests for ``DataTableBlock.get_context``, including the precedence fix."""

    def _make_value(self, **overrides: Any) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "table_id": "t1",
            "table_label": "Test",
            "show_controls": False,
            "per_page": "10",
            "table": _make_typed_table(["Col"], [["val"]]),
        }
        defaults.update(overrides)
        return defaults

    def test_none_parent_context_does_not_raise(self) -> None:
        """Regression: ``None`` parent_context must not cause ``AttributeError``."""
        block = DataTableBlock()
        context = block.get_context(self._make_value(), parent_context=None)
        self.assertIn("t", context)
        self.assertEqual(context["t"]["table_url"], "")

    def test_extracts_request_from_parent_context(self) -> None:
        block = DataTableBlock()
        request = RequestFactory().get("/")
        parent_context: dict[str, Any] = {"request": request}
        context = block.get_context(self._make_value(), parent_context=parent_context)
        self.assertIn("t", context)

    def test_resolves_page_from_parent_context(self) -> None:
        block = DataTableBlock()
        fake_page = SimpleNamespace(pk=42)
        parent_context: dict[str, Any] = {"page": fake_page}
        context = block.get_context(self._make_value(), parent_context=parent_context)
        expected_url = reverse(
            "cms:table_partial",
            kwargs={"page_pk": 42, "table_id": "t1"},
        )
        self.assertEqual(context["t"]["table_url"], expected_url)

    def test_falls_back_to_self_key(self) -> None:
        """When ``page`` is absent, ``self`` key is used for the page object."""
        block = DataTableBlock()
        fake_page = SimpleNamespace(pk=99)
        parent_context: dict[str, Any] = {"self": fake_page}
        context = block.get_context(self._make_value(), parent_context=parent_context)
        expected_url = reverse(
            "cms:table_partial",
            kwargs={"page_pk": 99, "table_id": "t1"},
        )
        self.assertEqual(context["t"]["table_url"], expected_url)


# ---------------------------------------------------------------------------
# View layer: table_partial endpoint
# ---------------------------------------------------------------------------


def _table_content_json(
    table_id: str = "test-table",
    *,
    rows: list[list[Any]] | None = None,
) -> str:
    """Return StreamField JSON containing one DataTableBlock."""
    if rows is None:
        rows = [["Alice", 95.0], ["Bob", 87.5], ["Charlie", 72.0]]
    return json.dumps([
        {
            "type": "data_table",
            "value": {
                "table_id": table_id,
                "table_label": "Test Table",
                "show_controls": True,
                "per_page": "10",
                "table": {
                    "columns": [
                        {"type": "text", "heading": "Name"},
                        {"type": "numeric", "heading": "Score"},
                    ],
                    "rows": [{"values": r} for r in rows],
                    "caption": "",
                },
            },
            "id": f"block-{table_id}",
        },
    ])


class TablePartialViewTest(TestCase):
    """Integration tests for the ``table_partial`` HTMX endpoint."""

    @classmethod
    def setUpTestData(cls) -> None:
        root = Page.get_first_root_node()
        # Wagtail's initial migration creates a default page with slug="home";
        # remove it via treebeard so the tree stays consistent.
        for child in root.get_children():
            child.delete()
        root = Page.get_first_root_node()
        cls.home = HomePage(title="Home", slug="home")
        root.add_child(instance=cls.home)

        cls.page = StandardPage(title="Test Page", slug="test-page")
        cls.page.content = _table_content_json(
            "scores",
            rows=[[f"student-{i}", float(i)] for i in range(15)],
        )
        cls.home.add_child(instance=cls.page)
        cls.page.save_revision().publish()

    def _url(self, page_pk: int | None = None, table_id: str = "scores") -> str:
        return reverse(
            "cms:table_partial",
            kwargs={"page_pk": page_pk or self.page.pk, "table_id": table_id},
        )

    def test_returns_200_for_valid_request(self) -> None:
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "student-0")

    def test_nonexistent_page_returns_404(self) -> None:
        resp = self.client.get(self._url(page_pk=99999))
        self.assertEqual(resp.status_code, 404)

    def test_nonexistent_table_id_returns_404(self) -> None:
        resp = self.client.get(self._url(table_id="no-such-table"))
        self.assertEqual(resp.status_code, 404)

    def test_search_filters_response(self) -> None:
        resp = self.client.get(self._url(), {"search": "student-3"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "student-3")
        self.assertNotContains(resp, "student-0")

    def test_pagination(self) -> None:
        resp = self.client.get(self._url(), {"page": "2", "per_page": "10"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "student-10")
        self.assertNotContains(resp, "student-0")

    def test_page_without_content_field_returns_404(self) -> None:
        """A page model that lacks a ``content`` StreamField should 404."""
        resp = self.client.get(
            reverse(
                "cms:table_partial",
                kwargs={"page_pk": self.home.pk, "table_id": "x"},
            ),
        )
        self.assertEqual(resp.status_code, 404)

    def test_login_restricted_page_returns_404_for_anonymous(self) -> None:
        """A page with a login view restriction should 404 for anonymous users."""
        PageViewRestriction.objects.create(
            page=self.page,
            restriction_type=PageViewRestriction.LOGIN,
        )
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 404)
