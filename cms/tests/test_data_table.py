"""Tests for the DataTableBlock feature: service, block, and view layers."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from wagtail.contrib.typed_table_block.blocks import TypedTable
from wagtail.models import Page, PageViewRestriction

from cms.blocks import DataTableBlock
from cms.pages import HomePage, StandardPage
from cms.services.data_table import extract_block_params, extract_table_data, get_table_context


def _make_typed_table(
    headers: list[str],
    rows: list[list[Any]],
    caption: str = "",
) -> SimpleNamespace:
    """Build a lightweight stand-in for a ``TypedTable`` bound value."""
    return SimpleNamespace(
        columns=[{"heading": h} for h in headers],
        row_data=[{"values": vals} for vals in rows],
        caption=caption,
    )


# ---------------------------------------------------------------------------
# Service layer: extract_table_data
# ---------------------------------------------------------------------------


class ExtractTableDataTest(SimpleTestCase):
    """Unit tests for ``extract_table_data``."""

    def test_none_returns_empty(self) -> None:
        """None input returns empty headers, rows, and caption."""
        headers, rows, caption = extract_table_data(None)
        self.assertEqual(headers, [])
        self.assertEqual(rows, [])
        self.assertEqual(caption, "")

    def test_empty_columns_returns_empty(self) -> None:
        """Table with no columns returns empty headers, rows, and caption."""
        table = SimpleNamespace(columns=[], row_data=[], caption="")
        headers, rows, caption = extract_table_data(table)
        self.assertEqual(headers, [])
        self.assertEqual(rows, [])
        self.assertEqual(caption, "")

    def test_extracts_headers_rows_and_caption(self) -> None:
        """Headers, rows, and caption are extracted from a well-formed table."""
        table = _make_typed_table(
            ["Name", "Score"],
            [["Alice", 95], ["Bob", 87]],
            caption="Student results",
        )
        headers, rows, caption = extract_table_data(table)
        self.assertEqual(headers, ["Name", "Score"])
        self.assertEqual(rows, [["Alice", 95], ["Bob", 87]])
        self.assertEqual(caption, "Student results")

    def test_preserves_rich_text_values(self) -> None:
        """RichTextValue-like objects must pass through untouched."""

        class _FakeRichText:
            def __html__(self) -> str:
                return "<b>bold</b>"

        rich = _FakeRichText()
        table = _make_typed_table(["Content"], [[rich]])
        _, rows, _ = extract_table_data(table)
        self.assertIs(rows[0][0], rich)


# ---------------------------------------------------------------------------
# Service layer: get_table_context
# ---------------------------------------------------------------------------


class GetTableContextTest(SimpleTestCase):
    """Unit tests for ``get_table_context``."""

    def setUp(self) -> None:
        """Create a 30-row dataset for pagination tests."""
        self.factory = RequestFactory()
        self.headers = ["Name", "Value"]
        self.rows: list[list[Any]] = [[f"item-{i}", i] for i in range(30)]

    def test_returns_all_expected_keys(self) -> None:
        """Returned dict contains every key the templates rely on."""
        ctx = get_table_context(
            request=None,
            rows=self.rows,
            headers=self.headers,
            caption="Test",
            table_url="/test/",
            table_id="tbl",
        )
        expected_keys = {
            "table_id",
            "caption",
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
        """None request falls back to default search, per_page, and page."""
        ctx = get_table_context(
            request=None,
            rows=self.rows,
            headers=self.headers,
            caption="",
            table_url="/test/",
        )
        self.assertEqual(ctx["search"], "")
        self.assertEqual(ctx["per_page"], 10)
        self.assertEqual(ctx["total_count"], 30)

    def test_caption_passed_through(self) -> None:
        """The caption string is included in the returned context."""
        ctx = get_table_context(
            request=None,
            rows=[],
            headers=[],
            caption="My Table",
            table_url="/t/",
        )
        self.assertEqual(ctx["caption"], "My Table")

    def test_search_filters_rows(self) -> None:
        """Search term keeps only matching rows."""
        request = self.factory.get("/", {"search": "item-5"})
        ctx = get_table_context(
            request=request,
            rows=self.rows,
            headers=self.headers,
            caption="",
            table_url="/test/",
        )
        self.assertEqual(ctx["total_count"], 1)
        self.assertEqual(list(ctx["page_obj"])[0], ["item-5", 5])

    def test_search_strips_html_tags(self) -> None:
        """Search matches against plain text after stripping HTML tags."""
        rows: list[list[Any]] = [["<b>Alpha</b>", 1], ["Beta", 2]]
        request = self.factory.get("/", {"search": "alpha"})
        ctx = get_table_context(
            request=request,
            rows=rows,
            headers=["Name", "Val"],
            caption="",
            table_url="/test/",
        )
        self.assertEqual(ctx["total_count"], 1)

    def test_search_is_case_insensitive(self) -> None:
        """Search matching ignores case."""
        request = self.factory.get("/", {"search": "ITEM-0"})
        ctx = get_table_context(
            request=request,
            rows=self.rows,
            headers=self.headers,
            caption="",
            table_url="/test/",
        )
        self.assertEqual(ctx["total_count"], 1)

    def test_invalid_per_page_falls_back_to_default(self) -> None:
        """A per_page value not in per_page_options reverts to the default."""
        request = self.factory.get("/", {"per_page": "999"})
        ctx = get_table_context(
            request=request,
            rows=self.rows,
            headers=self.headers,
            caption="",
            table_url="/test/",
            per_page_default=10,
        )
        self.assertEqual(ctx["per_page"], 10)

    def test_non_numeric_per_page_falls_back(self) -> None:
        """Non-numeric per_page reverts to the default."""
        request = self.factory.get("/", {"per_page": "abc"})
        ctx = get_table_context(
            request=request,
            rows=self.rows,
            headers=self.headers,
            caption="",
            table_url="/test/",
        )
        self.assertEqual(ctx["per_page"], 10)

    def test_pagination_defaults_to_page_one(self) -> None:
        """Without a page param the first page is returned."""
        ctx = get_table_context(
            request=None,
            rows=self.rows,
            headers=self.headers,
            caption="",
            table_url="/test/",
            per_page_default=10,
        )
        self.assertEqual(ctx["page_obj"].number, 1)
        self.assertEqual(ctx["start_index"], 1)
        self.assertEqual(ctx["end_index"], 10)

    def test_explicit_page_number(self) -> None:
        """An explicit page param selects the corresponding page."""
        request = self.factory.get("/", {"page": "2"})
        ctx = get_table_context(
            request=request,
            rows=self.rows,
            headers=self.headers,
            caption="",
            table_url="/test/",
            per_page_default=10,
        )
        self.assertEqual(ctx["page_obj"].number, 2)
        self.assertEqual(ctx["start_index"], 11)

    def test_invalid_page_number_defaults_to_first(self) -> None:
        """Non-numeric page number falls back to page 1."""
        request = self.factory.get("/", {"page": "xyz"})
        ctx = get_table_context(
            request=request,
            rows=self.rows,
            headers=self.headers,
            caption="",
            table_url="/test/",
        )
        self.assertEqual(ctx["page_obj"].number, 1)

    def test_out_of_range_page_returns_last(self) -> None:
        """Page number beyond the last page returns the last page."""
        request = self.factory.get("/", {"page": "999"})
        ctx = get_table_context(
            request=request,
            rows=self.rows,
            headers=self.headers,
            caption="",
            table_url="/test/",
            per_page_default=10,
        )
        self.assertEqual(ctx["page_obj"].number, 3)

    def test_show_controls_passed_through(self) -> None:
        """The show_controls flag is included in the returned context."""
        ctx = get_table_context(
            request=None,
            rows=[],
            headers=[],
            caption="",
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
            caption="",
            table_url="/test/",
            per_page_default=10,
            show_controls=False,
        )
        self.assertEqual(ctx["total_count"], 30)
        self.assertEqual(len(list(ctx["page_obj"])), 30)
        self.assertEqual(ctx["page_obj"].paginator.num_pages, 1)

    def test_empty_rows_returns_zero_counts(self) -> None:
        """Empty dataset yields zero for total, start, and end index."""
        ctx = get_table_context(
            request=None,
            rows=[],
            headers=[],
            caption="",
            table_url="/t/",
        )
        self.assertEqual(ctx["total_count"], 0)
        self.assertEqual(ctx["start_index"], 0)
        self.assertEqual(ctx["end_index"], 0)


# ---------------------------------------------------------------------------
# Service layer: extract_block_params
# ---------------------------------------------------------------------------


class ExtractBlockParamsTest(SimpleTestCase):
    """Unit tests for ``extract_block_params``."""

    def test_normal_values(self) -> None:
        """Standard block values are converted correctly."""
        params = extract_block_params(
            {
                "table_id": "tbl",
                "per_page": "25",
                "show_controls": True,
            }
        )
        self.assertEqual(params["table_id"], "tbl")
        self.assertEqual(params["per_page_default"], 25)
        self.assertTrue(params["show_controls"])

    def test_empty_per_page_falls_back_to_default(self) -> None:
        """Empty per_page (from optional ChoiceBlock) falls back to 10."""
        params = extract_block_params(
            {
                "table_id": "tbl",
                "per_page": "",
                "show_controls": False,
            }
        )
        self.assertEqual(params["per_page_default"], 10)

    def test_missing_per_page_falls_back_to_default(self) -> None:
        """Missing per_page key falls back to 10."""
        params = extract_block_params(
            {
                "table_id": "tbl",
                "show_controls": False,
            }
        )
        self.assertEqual(params["per_page_default"], 10)


# ---------------------------------------------------------------------------
# Block layer: DataTableBlock.get_context
# ---------------------------------------------------------------------------


class DataTableBlockContextTest(SimpleTestCase):
    """Tests for ``DataTableBlock.get_context``."""

    def _make_value(self, **overrides: str | int | bool | SimpleNamespace) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "table_id": "t1",
            "show_controls": False,
            "per_page": "10",
            "table": _make_typed_table(["Col"], [["val"]], caption="Test caption"),
        }
        defaults.update(overrides)
        return defaults

    def test_none_parent_context_does_not_raise(self) -> None:
        """Regression: ``None`` parent_context must not cause ``AttributeError``."""
        block = DataTableBlock()
        context = block.get_context(self._make_value(), parent_context=None)
        self.assertIn("t", context)
        self.assertEqual(context["t"]["table_url"], "")

    def test_caption_forwarded_to_context(self) -> None:
        """Caption from the TypedTable is included in the template context."""
        block = DataTableBlock()
        context = block.get_context(self._make_value(), parent_context=None)
        self.assertEqual(context["t"]["caption"], "Test caption")

    def test_extracts_request_from_parent_context(self) -> None:
        """Request object is forwarded from parent_context to get_table_context."""
        block = DataTableBlock()
        request = RequestFactory().get("/")
        parent_context: dict[str, Any] = {"request": request}
        context = block.get_context(self._make_value(), parent_context=parent_context)
        self.assertIn("t", context)

    def test_resolves_page_from_parent_context(self) -> None:
        """Page PK from ``page`` key is used to build the table_url."""
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
# Block layer: DataTableBlock.clean
# ---------------------------------------------------------------------------


class DataTableBlockCleanTest(SimpleTestCase):
    """Tests for ``DataTableBlock.clean`` auto-filling table_id from caption."""

    @staticmethod
    def _empty_table(caption: str = "") -> TypedTable:
        """Return a normalised TypedTable that survives StructBlock.clean()."""
        block = DataTableBlock()
        table = block.child_blocks["table"].normalize(None)
        table.caption = caption
        return table

    def test_auto_generates_table_id_from_caption(self) -> None:
        """Empty table_id is filled with the slugified table caption."""
        block = DataTableBlock()
        value = {
            "table_id": "",
            "show_controls": False,
            "per_page": "",
            "table": self._empty_table("Student Scores 2026"),
        }
        cleaned = block.clean(value)
        self.assertEqual(cleaned["table_id"], "student-scores-2026")

    def test_preserves_explicit_table_id(self) -> None:
        """A non-empty table_id is kept as-is."""
        block = DataTableBlock()
        value = {
            "table_id": "custom-id",
            "show_controls": False,
            "per_page": "",
            "table": self._empty_table("Student Scores"),
        }
        cleaned = block.clean(value)
        self.assertEqual(cleaned["table_id"], "custom-id")

    def test_auto_id_truncated_to_60_chars(self) -> None:
        """Auto-generated table_id is truncated to the max_length of 60."""
        block = DataTableBlock()
        value = {
            "table_id": "",
            "show_controls": False,
            "per_page": "",
            "table": self._empty_table("a" * 100),
        }
        cleaned = block.clean(value)
        self.assertLessEqual(len(cleaned["table_id"]), 60)


# ---------------------------------------------------------------------------
# View layer: table_partial endpoint
# ---------------------------------------------------------------------------


def _table_content_json(
    table_id: str = "test-table",
    *,
    rows: list[list[Any]] | None = None,
    caption: str = "Test Table",
) -> str:
    """Return StreamField JSON containing one DataTableBlock."""
    if rows is None:
        rows = [["Alice", 95.0, 25], ["Bob", 87.5, 30], ["Charlie", 72.0, 22]]
    return json.dumps(
        [
            {
                "type": "data_table",
                "value": {
                    "table_id": table_id,
                    "show_controls": True,
                    "per_page": "10",
                    "table": {
                        "columns": [
                            {"type": "text", "heading": "Name"},
                            {"type": "numeric", "heading": "Score"},
                            {"type": "integer", "heading": "Age"},
                        ],
                        "rows": [{"values": r} for r in rows],
                        "caption": caption,
                    },
                },
                "id": f"block-{table_id}",
            },
        ]
    )


class TablePartialViewTest(TestCase):
    """Integration tests for the ``table_partial`` HTMX endpoint."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Create a published StandardPage with a 15-row data table."""
        root = Page.get_first_root_node()
        for child in root.get_children():
            child.delete()
        root = Page.get_first_root_node()
        cls.home = HomePage(title="Home", slug="home")
        root.add_child(instance=cls.home)

        cls.page = StandardPage(title="Test Page", slug="test-page")
        cls.page.content = _table_content_json(
            "scores",
            rows=[[f"student-{i}", float(i), 18 + i] for i in range(15)],
            caption="Student Scores",
        )
        cls.home.add_child(instance=cls.page)
        cls.page.save_revision().publish()

    def _url(self, page_pk: int | None = None, table_id: str = "scores") -> str:
        return reverse(
            "cms:table_partial",
            kwargs={"page_pk": page_pk or self.page.pk, "table_id": table_id},
        )

    def test_returns_200_for_valid_request(self) -> None:
        """Valid page and table_id returns 200 with table content."""
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "student-0")

    def test_caption_rendered_in_response(self) -> None:
        """The table caption appears in the rendered HTML."""
        resp = self.client.get(self._url())
        self.assertContains(resp, "<caption")
        self.assertContains(resp, "Student Scores")

    def test_nonexistent_page_returns_404(self) -> None:
        """Non-existent page PK returns 404."""
        resp = self.client.get(self._url(page_pk=99999))
        self.assertEqual(resp.status_code, 404)

    def test_nonexistent_table_id_returns_404(self) -> None:
        """Unrecognised table_id on an existing page returns 404."""
        resp = self.client.get(self._url(table_id="no-such-table"))
        self.assertEqual(resp.status_code, 404)

    def test_search_filters_response(self) -> None:
        """Search param filters the rendered table rows."""
        resp = self.client.get(self._url(), {"search": "student-3"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "student-3")
        self.assertNotContains(resp, "student-0")

    def test_pagination(self) -> None:
        """Page 2 shows rows 11-15 and omits rows 0-9."""
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

    def test_integer_column_renders_without_decimals(self) -> None:
        """Integer column values render without a decimal point."""
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "<td>18</td>")
        self.assertNotContains(resp, "18.0")

    def test_login_restricted_page_returns_404_for_anonymous(self) -> None:
        """A page with a login view restriction should 404 for anonymous users."""
        PageViewRestriction.objects.create(
            page=self.page,
            restriction_type=PageViewRestriction.LOGIN,
        )
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 404)
