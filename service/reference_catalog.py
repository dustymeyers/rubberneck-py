"""Unified catalog for short D&D 5e SRD reference material."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import discord

from service.api_client import DnDAPI, ResourceNotFound


AUTOCOMPLETE_LIMIT = 25
AUTOCOMPLETE_LABEL_LIMIT = 100
REFERENCE_VALUE_SEPARATOR = ":"


@dataclass(frozen=True)
class ReferenceType:
    key: str
    label: str
    endpoint: str


RULE = ReferenceType(key="rule", label="Rule", endpoint="rule-sections")
CONDITION = ReferenceType(key="condition", label="Condition", endpoint="conditions")
REFERENCE_TYPES = (RULE, CONDITION)


@dataclass(frozen=True)
class ReferenceEntry:
    index: str
    name: str
    url: str
    reference_type: ReferenceType

    @property
    def value(self) -> str:
        return f"{self.reference_type.key}{REFERENCE_VALUE_SEPARATOR}{self.index}"

    @property
    def choice_name(self) -> str:
        label = f"{self.name} — {self.reference_type.label}"
        return label[:AUTOCOMPLETE_LABEL_LIMIT]


class ReferenceCatalog:
    """Loads, resolves, and indexes heterogeneous SRD reference resources."""

    def __init__(
        self,
        client: DnDAPI,
        reference_types: tuple[ReferenceType, ...] = REFERENCE_TYPES,
    ) -> None:
        self.client = client
        self.reference_types = reference_types
        self.entries: list[ReferenceEntry] = []
        self.autocomplete_index: dict[str, tuple[discord.OptionChoice, ...]] = {}

    async def load(self) -> None:
        resource_lists = await asyncio.gather(
            *(self.client.list_resources(item.endpoint) for item in self.reference_types)
        )
        self.entries = [
            ReferenceEntry(
                index=resource.index,
                name=resource.name,
                url=resource.url,
                reference_type=reference_type,
            )
            for reference_type, resources in zip(self.reference_types, resource_lists)
            for resource in resources
        ]
        self.autocomplete_index = self._build_autocomplete_index()

    def choices(
        self,
        query: str,
        reference_type: ReferenceType | None = None,
    ) -> list[discord.OptionChoice]:
        key = self._autocomplete_key(query, reference_type)
        return list(self.autocomplete_index.get(key, ()))

    async def resolve(
        self,
        term: str,
        reference_type: ReferenceType | None = None,
    ) -> tuple[ReferenceEntry, dict]:
        entry = self.find(term, reference_type)
        if entry is None:
            raise ResourceNotFound(f"No SRD reference found for '{term}'.")
        payload = await self.client.get_resource(entry.reference_type.endpoint, entry.index)
        return entry, payload

    def find(
        self,
        term: str,
        reference_type: ReferenceType | None = None,
    ) -> ReferenceEntry | None:
        encoded_type, encoded_index = self._decode_value(term)
        if encoded_type is not None:
            reference_type = encoded_type
            term = encoded_index

        candidates = self._entries_for(reference_type)
        query = self._normalise(term)
        ranked = [
            (rank, position, entry)
            for position, entry in enumerate(candidates)
            if (rank := self._rank(entry, query)) is not None
        ]
        if not ranked:
            return None
        return min(ranked, key=lambda item: (item[0], item[1]))[2]

    def _build_autocomplete_index(self) -> dict[str, tuple[discord.OptionChoice, ...]]:
        index: dict[str, tuple[discord.OptionChoice, ...]] = {}
        scopes = ((None, self.entries),) + tuple(
            (reference_type, self._entries_for(reference_type))
            for reference_type in self.reference_types
        )
        for reference_type, entries in scopes:
            queries = {""}
            for entry in entries:
                for value in (self._normalise(entry.name), self._normalise(entry.index)):
                    queries.update(
                        value[start:end]
                        for start in range(len(value))
                        for end in range(start + 1, len(value) + 1)
                    )
            for query in queries:
                ranked = sorted(
                    (
                        (rank, position, entry)
                        for position, entry in enumerate(entries)
                        if (rank := self._rank(entry, query)) is not None
                    ),
                    key=lambda item: (item[0], item[1]),
                )
                choices = tuple(
                    discord.OptionChoice(name=entry.choice_name, value=entry.value)
                    for _, _, entry in ranked[:AUTOCOMPLETE_LIMIT]
                )
                index[self._autocomplete_key(query, reference_type)] = choices
        return index

    def _entries_for(self, reference_type: ReferenceType | None) -> list[ReferenceEntry]:
        if reference_type is None:
            return self.entries
        return [entry for entry in self.entries if entry.reference_type == reference_type]

    def _decode_value(self, value: str) -> tuple[ReferenceType | None, str]:
        if REFERENCE_VALUE_SEPARATOR not in value:
            return None, value
        type_key, index = value.split(REFERENCE_VALUE_SEPARATOR, maxsplit=1)
        reference_type = next(
            (item for item in self.reference_types if item.key == type_key),
            None,
        )
        return reference_type, index if reference_type else value

    @staticmethod
    def _normalise(value: str) -> str:
        return "-".join(value.strip().casefold().replace("_", " ").split())

    @classmethod
    def _rank(cls, entry: ReferenceEntry, query: str) -> int | None:
        name = cls._normalise(entry.name)
        index = cls._normalise(entry.index)
        if query in (name, index):
            return 0
        if name.startswith(query) or index.startswith(query):
            return 1
        if query in name or query in index:
            return 2
        return None

    @staticmethod
    def _autocomplete_key(
        query: str,
        reference_type: ReferenceType | None,
    ) -> str:
        scope = reference_type.key if reference_type else "all"
        return f"{scope}:{ReferenceCatalog._normalise(query)}"
