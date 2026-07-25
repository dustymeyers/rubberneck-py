import pytest

from rubberneck.services.reference_catalog import CONDITION, RULE, ReferenceEntry
from rubberneck.services.reference_search import (
    MAX_SEARCH_RESULTS,
    InvalidSearchQuery,
    ReferenceSearchIndex,
    normalize_text,
)


class FakeSearchClient:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    async def get_resource(self, endpoint, index):
        self.calls.append((endpoint, index))
        return self.payloads[(endpoint, index)]


def entry(index, name, reference_type=RULE):
    return ReferenceEntry(
        index,
        name,
        f"/{reference_type.endpoint}/{index}",
        reference_type,
    )


@pytest.mark.asyncio
async def test_index_loads_full_descriptions_then_searches_without_network():
    entries = [
        entry("unseen-attackers", "Unseen Attackers and Targets"),
        entry("invisible", "Invisible", CONDITION),
    ]
    client = FakeSearchClient(
        {
            ("rule-sections", "unseen-attackers"): {
                "name": "Unseen Attackers and Targets",
                "desc": "When you attack a target that you can't see, you have disadvantage.",
            },
            ("conditions", "invisible"): {
                "name": "Invisible",
                "desc": ["An invisible creature is impossible to see without magic."],
            },
        }
    )
    index = ReferenceSearchIndex(client)

    await index.load(entries)
    calls_after_load = list(client.calls)
    results = index.search("attack target see")
    payload = index.payload_for(entries[1])

    assert results[0].entry.index == "unseen-attackers"
    assert payload["name"] == "Invisible"
    assert payload["desc"] == [
        "An invisible creature is impossible to see without magic."
    ]
    assert client.calls == calls_after_load


@pytest.mark.asyncio
async def test_title_match_ranks_above_description_only_match():
    entries = [
        entry("cover", "Cover"),
        entry("other", "Other Defenses"),
    ]
    client = FakeSearchClient(
        {
            ("rule-sections", "cover"): {
                "name": "Cover",
                "desc": "Walls can protect a target.",
            },
            ("rule-sections", "other"): {
                "name": "Other Defenses",
                "desc": "This description discusses cover in detail.",
            },
        }
    )
    index = ReferenceSearchIndex(client)
    await index.load(entries)

    results = index.search("cover")

    assert [result.entry.index for result in results] == ["cover", "other"]
    assert results[0].score > results[1].score


@pytest.mark.asyncio
async def test_exact_phrase_ranks_ahead_of_separated_terms():
    entries = [
        entry("phrase", "Phrase"),
        entry("separated", "Separated"),
    ]
    client = FakeSearchClient(
        {
            ("rule-sections", "phrase"): {
                "name": "Phrase",
                "desc": "You may attack while hidden from the target.",
            },
            ("rule-sections", "separated"): {
                "name": "Separated",
                "desc": "While hidden, you may later attack the target.",
            },
        }
    )
    index = ReferenceSearchIndex(client)
    await index.load(entries)

    results = index.search("attack while hidden")

    assert [result.entry.index for result in results] == ["phrase", "separated"]
    assert results[0].score > results[1].score


@pytest.mark.asyncio
async def test_prefix_terms_match_but_arbitrary_substrings_do_not():
    entries = [entry("attacking", "Attacking"), entry("pattern", "Pattern")]
    client = FakeSearchClient(
        {
            ("rule-sections", "attacking"): {
                "name": "Attacking",
                "desc": "Attackers make attacks.",
            },
            ("rule-sections", "pattern"): {
                "name": "Pattern",
                "desc": "A decorative pattern.",
            },
        }
    )
    index = ReferenceSearchIndex(client)
    await index.load(entries)

    assert index.search("attac")[0].entry.index == "attacking"
    assert index.search("tack") == []


@pytest.mark.asyncio
async def test_excerpt_highlights_matches_without_preserving_source_markdown():
    target = "attack while hidden"
    description = (
        "**Opening text** with [a link](https://example.test). "
        + ("Filler sentence. " * 30)
        + f"You can {target} when unseen. Final sentence."
    )
    document = entry("hidden", "Hidden")
    client = FakeSearchClient(
        {
            ("rule-sections", "hidden"): {
                "name": "Hidden",
                "desc": description,
            }
        }
    )
    index = ReferenceSearchIndex(client)
    await index.load([document])

    result = index.search(target)[0]

    assert "**attack while hidden**" in result.excerpt
    assert "https://example.test" not in result.excerpt
    assert len(result.excerpt) <= 310
    assert result.excerpt.startswith("…")


@pytest.mark.asyncio
async def test_excerpt_ignores_query_inside_an_unrelated_longer_word():
    description = (
        "A counterattack is mentioned in an unrelated opening sentence. "
        + ("Filler sentence. " * 30)
        + "Later, an attack has advantage."
    )
    document = entry("attack", "Attack")
    client = FakeSearchClient(
        {
            ("rule-sections", "attack"): {
                "name": "Attack",
                "desc": description,
            }
        }
    )
    index = ReferenceSearchIndex(client)
    await index.load([document])

    result = index.search("attack")[0]

    assert "**attack** has advantage" in result.excerpt
    assert "counterattack" not in result.excerpt


@pytest.mark.asyncio
async def test_result_limit_and_deterministic_title_tiebreak():
    entries = [entry(f"item-{number:02}", f"Item {number:02}") for number in range(25)]
    client = FakeSearchClient(
        {
            ("rule-sections", item.index): {
                "name": item.name,
                "desc": "A shared searchable description.",
            }
            for item in entries
        }
    )
    index = ReferenceSearchIndex(client)
    await index.load(entries)

    results = index.search("shared")

    assert len(results) == MAX_SEARCH_RESULTS
    assert [result.entry.name for result in results[:3]] == [
        "Item 00",
        "Item 01",
        "Item 02",
    ]


@pytest.mark.parametrize("query", ["", "a", "  !  ", "!aa"])
def test_short_or_empty_queries_are_rejected(query):
    index = ReferenceSearchIndex(FakeSearchClient({}))

    with pytest.raises(InvalidSearchQuery):
        index.search(query)


def test_normalization_uses_unicode_casefolding_and_punctuation_boundaries():
    assert normalize_text("  STRAẞE—Attack_hidden  ") == "strasse attack hidden"
