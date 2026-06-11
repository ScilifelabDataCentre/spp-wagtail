"""Search Europe PMC for publications associated with MetaboLights."""

import csv
import time
from pathlib import Path

import requests

BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
BASE_FILTER = '((ACCESSION_TYPE:"metabolights") OR (LABS_PUBS:"1782"))'


def build_query(author_name: str) -> str:
    """Build a Europe PMC query string for the given author name."""
    author_name = (author_name or "").strip()
    if not author_name:
        raise ValueError("author_name is empty")
    return f'{BASE_FILTER} AND AUTH:"{author_name}"'


def search_europe_pmc(query: str, page_size: int = 1000, sleep_s: float = 0.1) -> list[dict]:
    """Retrieve all Europe PMC results for a query using cursor pagination.

    Returns a list of result records.
    """
    cursor_mark = "*"
    all_results = []

    while True:
        params = {
            "query": query,
            "format": "json",
            "pageSize": page_size,
            "cursorMark": cursor_mark,
            "resultType": "core",
        }

        response = requests.get(BASE_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        results = data.get("resultList", {}).get("result", [])
        all_results.extend(results)

        next_cursor = data.get("nextCursorMark")
        if not results or not next_cursor or next_cursor == cursor_mark:
            break

        cursor_mark = next_cursor
        time.sleep(sleep_s)

    return all_results


def safe_get(record: dict, key: str) -> str:
    """Return record[key] as a string, or an empty string if missing or None."""
    value = record.get(key, "")
    if value is None:
        return ""
    return value


def flatten_paper(author_name: str, query: str, paper: dict) -> dict:
    """Flatten a Europe PMC result record into a row dict for CSV output."""
    return {
        "input_author": author_name,
        "query": query,
        "epmc_id": safe_get(paper, "id"),
        "source": safe_get(paper, "source"),
        "pmid": safe_get(paper, "pmid"),
        "pmcid": safe_get(paper, "pmcid"),
        "doi": safe_get(paper, "doi"),
        "title": safe_get(paper, "title"),
        "author_string": safe_get(paper, "authorString"),
        "journal": safe_get(paper, "journalTitle"),
        "pub_year": safe_get(paper, "pubYear"),
        "first_publication_date": safe_get(paper, "firstPublicationDate"),
        "cited_by_count": safe_get(paper, "citedByCount"),
        "is_open_access": safe_get(paper, "isOpenAccess"),
    }


def read_authors_from_csv(input_csv: str, author_column: str) -> list[str]:
    """Read unique, non-empty author names from a column in a CSV file."""
    authors = []
    seen = set()

    with Path(input_csv).open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if author_column not in reader.fieldnames:
            raise ValueError(
                f"Column '{author_column}' not found. Available columns: {reader.fieldnames}"
            )

        for row in reader:
            author = (row.get(author_column) or "").strip()
            if not author:
                continue
            if author not in seen:
                seen.add(author)
                authors.append(author)

    return authors


def main() -> None:
    """Run the Europe PMC author search and write results to CSV files."""
    input_csv = "authors.csv"
    author_column = "author"
    papers_output_csv = "europepmc_metabolights_papers.csv"
    summary_output_csv = "europepmc_metabolights_summary.csv"

    authors = read_authors_from_csv(input_csv, author_column)

    paper_rows = []
    summary_rows = []

    for idx, author_name in enumerate(authors, start=1):
        try:
            query = build_query(author_name)
            results = search_europe_pmc(query)

            print(f"[{idx}/{len(authors)}] {author_name}: {len(results)} matches")

            for paper in results:
                paper_rows.append(flatten_paper(author_name, query, paper))

            summary_rows.append(
                {
                    "input_author": author_name,
                    "query": query,
                    "match_count": len(results),
                }
            )

        except Exception as e:
            print(f"[{idx}/{len(authors)}] ERROR for {author_name}: {e}")
            summary_rows.append(
                {
                    "input_author": author_name,
                    "query": "",
                    "match_count": "",
                    "error": str(e),
                }
            )

    paper_fieldnames = [
        "input_author",
        "query",
        "epmc_id",
        "source",
        "pmid",
        "pmcid",
        "doi",
        "title",
        "author_string",
        "journal",
        "pub_year",
        "first_publication_date",
        "cited_by_count",
        "is_open_access",
    ]

    with Path(papers_output_csv).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=paper_fieldnames)
        writer.writeheader()
        writer.writerows(paper_rows)

    summary_fieldnames = ["input_author", "query", "match_count", "error"]
    with Path(summary_output_csv).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    print()
    print(f"Wrote {len(paper_rows)} paper rows to {papers_output_csv}")
    print(f"Wrote {len(summary_rows)} summary rows to {summary_output_csv}")


if __name__ == "__main__":
    main()
