from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup, FeatureNotFound

from ..models.records import PartId
from ..utils.ids import question_number_from_summa_url
from ..utils.text import normalize_text, visible_text
from .source import NewAdventClient

PART_INDEX_URLS: dict[PartId, str] = {
    "i-ii": "https://www.newadvent.org/summa/2.htm",
    "ii-ii": "https://www.newadvent.org/summa/3.htm",
}

QUESTION_RANGES: dict[PartId, range] = {
    "i-ii": range(1, 115),
    "ii-ii": range(1, 183),
}


@dataclass(frozen=True)
class ScopeEntry:
    part_id: PartId
    question_number: int
    source_part_url: str
    source_url: str
    question_title_hint: str | None = None


def is_in_scope(part_id: PartId, question_number: int) -> bool:
    return question_number in QUESTION_RANGES.get(part_id, range(0))


def parse_part_index_html(
    part_id: PartId,
    source_part_url: str,
    html_text: str,
) -> list[ScopeEntry]:
    try:
        soup = BeautifulSoup(html_text, "lxml")
    except FeatureNotFound:
        soup = BeautifulSoup(html_text, "html.parser")
    seen: set[int] = set()
    entries: list[ScopeEntry] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if not isinstance(href, str):
            continue
        absolute_url = urljoin(source_part_url, href)
        try:
            parsed_part_id, question_number = question_number_from_summa_url(absolute_url)
        except ValueError:
            continue
        if parsed_part_id != part_id or not is_in_scope(part_id, question_number):
            continue
        if question_number in seen:
            continue
        seen.add(question_number)
        entries.append(
            ScopeEntry(
                part_id=part_id,
                question_number=question_number,
                source_part_url=source_part_url,
                source_url=absolute_url,
                question_title_hint=normalize_text(visible_text(anchor)),
            )
        )
    return sorted(entries, key=lambda entry: entry.question_number)


def build_scope_manifest(refresh_cache: bool = False) -> list[ScopeEntry]:
    manifest: list[ScopeEntry] = []
    with NewAdventClient() as client:
        for part_id, source_part_url in PART_INDEX_URLS.items():
            html_text = client.fetch_text(source_part_url, refresh_cache=refresh_cache)
            manifest.extend(parse_part_index_html(part_id, source_part_url, html_text))
    return manifest
