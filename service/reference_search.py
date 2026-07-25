"""Deterministic in-memory full-text search for SRD references."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import re
import unicodedata

from service.api_client import DnDAPI
from service.reference_catalog import ReferenceEntry


MIN_SEARCH_CHARACTERS = 3
MIN_SEARCH_TOKEN_LENGTH = 2
MAX_SEARCH_RESULTS = 20
SEARCH_EXCERPT_LIMIT = 300

EXACT_TITLE_WEIGHT = 2_000
TITLE_PHRASE_WEIGHT = 1_000
ALL_TITLE_TERMS_WEIGHT = 500
EXACT_TITLE_TERM_WEIGHT = 100
TITLE_PREFIX_TERM_WEIGHT = 50
DESCRIPTION_PHRASE_WEIGHT = 400
ALL_DESCRIPTION_TERMS_WEIGHT = 200
EXACT_DESCRIPTION_TERM_WEIGHT = 20
DESCRIPTION_PREFIX_TERM_WEIGHT = 10

_MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MARKDOWN_DECORATION = re.compile(r"(?m)^\s{0,3}#{1,6}\s+|[*_~`>|]")
_BOUNDARY = re.compile(r"(?:\n\s*\n|(?<=[.!?])\s+)")


class InvalidSearchQuery(ValueError):
    """Raised when a query is too short to produce useful results."""


@dataclass(frozen=True)
class SearchDocument:
    entry: ReferenceEntry
    description: str
    title_text: str
    title_tokens: tuple[str, ...]
    description_text: str
    description_tokens: tuple[str, ...]
    source_name: str = ""
    source_description: str | tuple[str, ...] = ""


@dataclass(frozen=True)
class SearchResult:
    entry: ReferenceEntry
    score: int
    excerpt: str


class ReferenceSearchIndex:
    """Fully loaded reference content that searches without network access."""

    def __init__(self, client: DnDAPI) -> None:
        self.client = client
        self.documents: tuple[SearchDocument, ...] = ()

    async def load(self, entries: list[ReferenceEntry]) -> None:
        payloads = await asyncio.gather(
            *(
                self.client.get_resource(entry.reference_type.endpoint, entry.index)
                for entry in entries
            )
        )
        self.documents = tuple(
            self._document(entry, payload)
            for entry, payload in zip(entries, payloads)
        )

    def search(
        self,
        query: str,
        limit: int = MAX_SEARCH_RESULTS,
    ) -> list[SearchResult]:
        phrase, query_tokens = parse_query(query)
        ranked: list[tuple[int, str, str, str, SearchResult]] = []
        for document in self.documents:
            score = _score(document, phrase, query_tokens)
            if score is None:
                continue
            result = SearchResult(
                entry=document.entry,
                score=score,
                excerpt=_excerpt(document, phrase, query_tokens),
            )
            ranked.append(
                (
                    -score,
                    document.title_text,
                    document.entry.reference_type.key,
                    document.entry.index,
                    result,
                )
            )
        ranked.sort(key=lambda item: item[:4])
        return [item[4] for item in ranked[:limit]]

    def payload_for(self, entry: ReferenceEntry) -> dict:
        """Return locally indexed source content for a reference."""
        document = next(
            (
                document
                for document in self.documents
                if document.entry.value == entry.value
            ),
            None,
        )
        if document is None:
            raise KeyError(entry.value)
        description = document.source_description
        return {
            "index": entry.index,
            "name": document.source_name or entry.name,
            "desc": list(description) if isinstance(description, tuple) else description,
            "url": entry.url,
        }

    @staticmethod
    def _document(entry: ReferenceEntry, payload: dict) -> SearchDocument:
        source_description = payload.get("desc") or ""
        stored_description = (
            tuple(source_description)
            if isinstance(source_description, list)
            else source_description
        )
        description = plain_text(_description_text(source_description))
        source_name = payload.get("name") or entry.name
        title_text = normalize_text(source_name)
        description_text = normalize_text(description)
        return SearchDocument(
            entry=entry,
            description=description,
            title_text=title_text,
            title_tokens=tuple(title_text.split()),
            description_text=description_text,
            description_tokens=tuple(description_text.split()),
            source_name=source_name,
            source_description=stored_description,
        )


def parse_query(query: str) -> tuple[str, tuple[str, ...]]:
    phrase = normalize_text(query)
    tokens = tuple(dict.fromkeys(phrase.split()))
    if (
        len(phrase) < MIN_SEARCH_CHARACTERS
        or not tokens
        or max(map(len, tokens)) < MIN_SEARCH_TOKEN_LENGTH
    ):
        raise InvalidSearchQuery(
            "Search text must contain at least 3 characters and one word "
            "with at least 2 characters."
        )
    return phrase, tokens


def normalize_text(value: str) -> str:
    """Normalize text into case-folded Unicode letter and number tokens."""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    characters = (
        character if character.isalnum() else " " for character in normalized
    )
    return " ".join("".join(characters).split())


def plain_text(value: str) -> str:
    """Remove Markdown syntax while retaining readable content."""
    value = value.replace("\r\n", "\n")
    value = _MARKDOWN_LINK.sub(r"\1", value)
    value = _MARKDOWN_DECORATION.sub("", value)
    return re.sub(r"\s+", " ", value).strip()


def _description_text(value: str | list[str] | None) -> str:
    if isinstance(value, list):
        return "\n\n".join(part.strip() for part in value if part.strip())
    return value or ""


def _score(
    document: SearchDocument,
    phrase: str,
    query_tokens: tuple[str, ...],
) -> int | None:
    title_matches = [_term_match(term, document.title_tokens) for term in query_tokens]
    description_matches = [
        _term_match(term, document.description_tokens) for term in query_tokens
    ]
    combined_matches = [
        max(title_match, description_match)
        for title_match, description_match in zip(title_matches, description_matches)
    ]
    title_phrase = _contains_phrase(document.title_text, phrase)
    description_phrase = _contains_phrase(document.description_text, phrase)
    if not title_phrase and not description_phrase and not all(combined_matches):
        return None

    score = 0
    if document.title_text == phrase:
        score += EXACT_TITLE_WEIGHT
    if title_phrase:
        score += TITLE_PHRASE_WEIGHT
    if all(title_matches):
        score += ALL_TITLE_TERMS_WEIGHT
    score += sum(
        EXACT_TITLE_TERM_WEIGHT if match == 2 else TITLE_PREFIX_TERM_WEIGHT
        for match in title_matches
        if match
    )
    if description_phrase:
        score += DESCRIPTION_PHRASE_WEIGHT
    if all(description_matches):
        score += ALL_DESCRIPTION_TERMS_WEIGHT
    score += sum(
        EXACT_DESCRIPTION_TERM_WEIGHT
        if match == 2
        else DESCRIPTION_PREFIX_TERM_WEIGHT
        for match in description_matches
        if match
    )
    return score


def _term_match(term: str, tokens: tuple[str, ...]) -> int:
    if term in tokens:
        return 2
    if any(token.startswith(term) for token in tokens):
        return 1
    return 0


def _contains_phrase(text: str, phrase: str) -> bool:
    return f" {phrase} " in f" {text} "


def _excerpt(
    document: SearchDocument,
    phrase: str,
    query_tokens: tuple[str, ...],
) -> str:
    description = document.description
    if not description:
        return "No description is available for this reference."

    match = _best_match(description, phrase, query_tokens)
    if match is None:
        start, end = 0, min(len(description), SEARCH_EXCERPT_LIMIT)
    else:
        match_start, match_end = match
        start = max(0, match_start - SEARCH_EXCERPT_LIMIT // 2)
        end = min(len(description), start + SEARCH_EXCERPT_LIMIT)
        start = max(0, end - SEARCH_EXCERPT_LIMIT)
        start, end = _prefer_boundaries(description, start, end, match_start, match_end)

    excerpt = description[start:end].strip()
    highlighted = _highlight(excerpt, phrase, query_tokens)
    if start:
        highlighted = f"…{highlighted}"
    if end < len(description):
        highlighted = f"{highlighted}…"
    return highlighted


def _best_match(
    text: str,
    phrase: str,
    query_tokens: tuple[str, ...],
) -> tuple[int, int] | None:
    normalized, mapping = _normalize_with_mapping(text)
    phrase_match = re.search(
        rf"(?<!\w){re.escape(phrase)}(?!\w)",
        normalized,
    )
    if phrase_match:
        return (
            mapping[phrase_match.start()],
            mapping[phrase_match.end() - 1] + 1,
        )

    for term in query_tokens:
        exact = re.search(rf"(?<!\w){re.escape(term)}(?!\w)", normalized)
        if exact:
            return mapping[exact.start()], mapping[exact.end() - 1] + 1
    for term in query_tokens:
        prefix = re.search(rf"(?<!\w){re.escape(term)}\w*", normalized)
        if prefix:
            return mapping[prefix.start()], mapping[prefix.end() - 1] + 1
    return None


def _normalize_with_mapping(value: str) -> tuple[str, list[int]]:
    output: list[str] = []
    mapping: list[int] = []
    pending_space = False
    pending_index = 0
    for index, character in enumerate(value):
        expanded = unicodedata.normalize("NFKC", character).casefold()
        for item in expanded:
            if item.isalnum():
                if pending_space and output:
                    output.append(" ")
                    mapping.append(pending_index)
                output.append(item)
                mapping.append(index)
                pending_space = False
            else:
                pending_space = True
                pending_index = index
    return "".join(output), mapping


def _prefer_boundaries(
    text: str,
    start: int,
    end: int,
    match_start: int,
    match_end: int,
) -> tuple[int, int]:
    boundaries = [0]
    boundaries.extend(match.end() for match in _BOUNDARY.finditer(text))
    boundaries.append(len(text))
    earlier = [boundary for boundary in boundaries if start <= boundary <= match_start]
    later = [boundary for boundary in boundaries if match_end <= boundary <= end]
    if earlier:
        start = max(earlier)
    if later:
        end = min(later)
    return start, end


def _highlight(
    text: str,
    phrase: str,
    query_tokens: tuple[str, ...],
) -> str:
    terms = sorted({phrase, *query_tokens}, key=len, reverse=True)
    pattern = re.compile(
        rf"(?<!\w)({'|'.join(map(re.escape, terms))})\w*",
        flags=re.IGNORECASE,
    )
    parts: list[str] = []
    position = 0
    for match in pattern.finditer(text):
        parts.append(_escape_markdown(text[position : match.start()]))
        parts.append(f"**{_escape_markdown(match.group())}**")
        position = match.end()
    parts.append(_escape_markdown(text[position:]))
    return "".join(parts)


def _escape_markdown(value: str) -> str:
    return re.sub(r"([\\`*_\[\]()|>~])", r"\\\1", value)
