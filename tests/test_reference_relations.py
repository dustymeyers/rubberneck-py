from rubberneck.services.reference_catalog import CONDITION, RULE, ReferenceEntry
from rubberneck.services.reference_relations import ReferenceRelations


def entry(index, reference_type=RULE):
    return ReferenceEntry(
        index=index,
        name=index.replace("-", " ").title(),
        url=f"/{reference_type.endpoint}/{index}",
        reference_type=reference_type,
    )


def test_related_entries_preserve_explicit_order_and_limit():
    source = entry("source")
    first = entry("first")
    second = entry("second", CONDITION)
    relations = ReferenceRelations(
        {
            source.value: (
                first.value,
                second.value,
            )
        }
    )

    result = relations.related(source, [source, second, first], limit=1)

    assert result == [first]


def test_missing_relationship_targets_are_omitted_and_reported():
    source = entry("source")
    present = entry("present")
    relations = ReferenceRelations(
        {
            source.value: (
                present.value,
                "condition:removed",
            )
        }
    )

    assert relations.related(source, [source, present]) == [present]
    assert relations.missing_targets([source, present]) == {"condition:removed"}


def test_entry_without_relationships_has_no_related_results():
    source = entry("source")

    assert ReferenceRelations({}).related(source, [source]) == []


def test_relationship_target_can_continue_through_source_and_siblings():
    source = entry("source")
    first = entry("first")
    second = entry("second", CONDITION)
    relations = ReferenceRelations(
        {
            source.value: (
                first.value,
                second.value,
            )
        }
    )

    result = relations.related(first, [source, first, second])

    assert result == [source, second]
