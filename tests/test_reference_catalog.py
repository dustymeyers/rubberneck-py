from time import perf_counter

import pytest
import pytest_asyncio

from service.api_client import ResourceNotFound, ResourceReference
from service.reference_catalog import CONDITION, RULE, ReferenceCatalog, ReferenceEntry


class FakeClient:
    def __init__(self):
        self.resources = {
            "rule-sections": [
                ResourceReference("cover", "Cover", "/rule-sections/cover"),
                ResourceReference(
                    "making-an-attack",
                    "Making an Attack",
                    "/rule-sections/making-an-attack",
                ),
            ],
            "conditions": [
                ResourceReference("restrained", "Restrained", "/conditions/restrained"),
                ResourceReference("invisible", "Invisible", "/conditions/invisible"),
            ],
        }

    async def list_resources(self, endpoint):
        return self.resources[endpoint]

    async def get_resource(self, endpoint, index):
        return {"index": index, "name": index.title(), "desc": ["Description"]}


@pytest_asyncio.fixture
async def catalog():
    result = ReferenceCatalog(FakeClient())
    await result.load()
    return result


@pytest.mark.asyncio
async def test_catalog_loads_all_configured_reference_types(catalog):
    assert len(catalog.entries) == 4
    assert {entry.reference_type for entry in catalog.entries} == {RULE, CONDITION}


@pytest.mark.asyncio
async def test_exact_matches_rank_ahead_of_substring_matches(catalog):
    assert catalog.find("cover").index == "cover"
    assert catalog.find("attack").index == "making-an-attack"


@pytest.mark.asyncio
async def test_encoded_choice_resolves_its_resource_type(catalog):
    entry, payload = await catalog.resolve("condition:restrained")

    assert entry.reference_type == CONDITION
    assert payload["index"] == "restrained"


@pytest.mark.asyncio
async def test_explicit_scope_excludes_other_resource_types(catalog):
    assert catalog.find("restrained", RULE) is None
    assert catalog.find("restrained", CONDITION).index == "restrained"


@pytest.mark.asyncio
async def test_autocomplete_labels_include_resource_type(catalog):
    choices = catalog.choices("rest")

    assert [(choice.name, choice.value) for choice in choices] == [
        ("Restrained — Condition", "condition:restrained")
    ]


@pytest.mark.asyncio
async def test_missing_reference_raises_resource_not_found(catalog):
    with pytest.raises(ResourceNotFound):
        await catalog.resolve("definitely-not-real")


def test_ambiguous_names_have_distinct_typed_choices():
    catalog = ReferenceCatalog(FakeClient())
    catalog.entries = [
        ReferenceEntry("shared", "Shared", "/rules/shared", RULE),
        ReferenceEntry("shared", "Shared", "/conditions/shared", CONDITION),
    ]
    catalog.autocomplete_index = catalog._build_autocomplete_index()

    assert [(choice.name, choice.value) for choice in catalog.choices("shared")] == [
        ("Shared — Rule", "rule:shared"),
        ("Shared — Condition", "condition:shared"),
    ]


@pytest.mark.asyncio
async def test_autocomplete_index_matches_dynamic_ranking(catalog):
    queries = {"", "a", "attack", "king-an", "visible", "not-present"}

    for reference_type in (None, RULE, CONDITION):
        entries = catalog._entries_for(reference_type)
        for query in queries:
            normalized = catalog._normalise(query)
            expected = sorted(
                (
                    (rank, position, entry.value)
                    for position, entry in enumerate(entries)
                    if (rank := catalog._rank(entry, normalized)) is not None
                ),
                key=lambda item: (item[0], item[1]),
            )
            actual = [choice.value for choice in catalog.choices(query, reference_type)]
            assert actual == [value for _, _, value in expected]


@pytest.mark.asyncio
async def test_warm_autocomplete_lookup_stays_below_five_milliseconds(catalog):
    samples = []
    for _ in range(1_000):
        started = perf_counter()
        catalog.choices("attack")
        samples.append((perf_counter() - started) * 1_000)

    samples.sort()
    percentile_95 = samples[int(len(samples) * 0.95)]

    assert percentile_95 < 5
    assert catalog.autocomplete_metrics.query_count == len(catalog.autocomplete_index)
