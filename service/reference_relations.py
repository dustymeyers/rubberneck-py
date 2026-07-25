"""Curated, deterministic relationships between SRD references."""

from __future__ import annotations

from service.reference_catalog import ReferenceEntry

MAX_RELATED_REFERENCES = 5

REFERENCE_RELATIONSHIPS: dict[str, tuple[str, ...]] = {
    "rule:making-an-attack": (
        "rule:advantage-and-disadvantage",
        "rule:cover",
        "condition:invisible",
        "condition:prone",
        "condition:restrained",
    ),
    "rule:cover": (
        "rule:making-an-attack",
        "rule:actions-in-combat",
        "condition:invisible",
    ),
    "rule:movement-and-position": (
        "rule:movement",
        "rule:mounted-combat",
        "rule:underwater-combat",
        "condition:grappled",
        "condition:prone",
    ),
    "rule:movement": (
        "rule:movement-and-position",
        "condition:grappled",
        "condition:restrained",
    ),
    "rule:damage-and-healing": (
        "rule:resting",
        "condition:unconscious",
        "condition:exhaustion",
    ),
    "rule:casting-a-spell": (
        "rule:what-is-a-spell",
        "rule:actions-in-combat",
        "condition:incapacitated",
    ),
    "condition:invisible": (
        "rule:making-an-attack",
        "rule:advantage-and-disadvantage",
        "condition:blinded",
    ),
    "condition:prone": (
        "rule:making-an-attack",
        "rule:movement-and-position",
        "condition:grappled",
    ),
    "condition:restrained": (
        "rule:making-an-attack",
        "rule:movement",
        "condition:grappled",
    ),
    "condition:unconscious": (
        "rule:damage-and-healing",
        "condition:incapacitated",
        "condition:prone",
    ),
    "condition:incapacitated": (
        "rule:actions-in-combat",
        "rule:casting-a-spell",
        "condition:unconscious",
    ),
    "condition:grappled": (
        "rule:movement",
        "condition:prone",
        "condition:restrained",
    ),
}


class ReferenceRelations:
    """Resolve ordered relationship data against the currently loaded catalog."""

    def __init__(
        self,
        relationships: dict[str, tuple[str, ...]] = REFERENCE_RELATIONSHIPS,
    ) -> None:
        self.relationships = relationships

    def related(
        self,
        entry: ReferenceEntry,
        entries: list[ReferenceEntry],
        limit: int = MAX_RELATED_REFERENCES,
    ) -> list[ReferenceEntry]:
        by_value = {candidate.value: candidate for candidate in entries}
        related_values = list(self.relationships.get(entry.value, ()))
        for source, targets in self.relationships.items():
            if entry.value not in targets:
                continue
            related_values.append(source)
            related_values.extend(targets)
        ordered_values = tuple(
            dict.fromkeys(value for value in related_values if value != entry.value)
        )
        return [by_value[value] for value in ordered_values if value in by_value][
            :limit
        ]

    def missing_targets(self, entries: list[ReferenceEntry]) -> set[str]:
        available = {entry.value for entry in entries}
        return {
            target
            for targets in self.relationships.values()
            for target in targets
            if target not in available
        }
