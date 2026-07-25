import pytest

from rubberneck.cogs.rules import (
    EMPTY_REFERENCE_DESCRIPTION,
    RULE_PAGE_DESCRIPTION_LIMIT,
    Rules,
    description_text,
    format_reference_description,
    format_rule_description,
    reference_embeds,
    reference_list_embeds,
    reference_list_results,
    search_result_embeds,
    split_description,
)
from rubberneck.services.reference_catalog import CONDITION, RULE, ReferenceEntry
from rubberneck.services.reference_search import SearchResult


class TestRuleFormatting:
    def test_short_description_is_unchanged(self):
        assert split_description("Short rule.") == ["Short rule."]

    def test_long_description_respects_embed_limit(self):
        chunks = split_description(("A useful sentence. " * 500).strip(), limit=200)
        assert len(chunks) > 1
        assert all(len(chunk) <= 200 for chunk in chunks)

    def test_empty_description_has_fallback(self):
        assert split_description("") == [EMPTY_REFERENCE_DESCRIPTION]

    def test_default_pages_are_sized_for_readability(self):
        chunks = split_description(("Readable paragraph. " * 300).strip())

        assert len(chunks) > 1
        assert all(len(chunk) <= RULE_PAGE_DESCRIPTION_LIMIT for chunk in chunks)

    def test_heading_stays_with_first_section_paragraph(self):
        text = (
            ("Earlier material. " * 65)
            + "\n\n**Important Section**\n\n"
            + ("Section details. " * 20)
        )

        pages = split_description(text, limit=300)

        heading_page = next(page for page in pages if "**Important Section**" in page)
        assert "Section details." in heading_page
        assert not any(page.endswith("**Important Section**") for page in pages)


def test_rule_option_is_a_real_string_type_with_autocomplete():
    option = next(option for option in Rules.rule.options if option.name == "name")

    assert option._raw_type is str
    assert option.autocomplete is Rules.rule_autocomplete


def test_rules_group_registers_lookup_search_and_list():
    commands = {command.name: command for command in Rules.rules.subcommands}

    assert set(commands) == {"lookup", "search", "list"}
    lookup_option = next(
        option for option in commands["lookup"].options if option.name == "term"
    )
    assert lookup_option._raw_type is str
    assert lookup_option.autocomplete is Rules.reference_autocomplete
    search_option = next(
        option for option in commands["search"].options if option.name == "text"
    )
    assert search_option._raw_type is str
    assert search_option.autocomplete is None
    type_option = next(
        option for option in commands["list"].options if option.name == "type"
    )
    assert [(choice.name, choice.value) for choice in type_option.choices] == [
        ("All references", "all"),
        ("Rule sections", "rules"),
        ("Conditions", "conditions"),
    ]


def test_rule_markdown_removes_duplicate_title_and_formats_headings():
    source = (
        "# Making an Attack\n\nIntro text.\n\n#### Modifiers to the Roll\n\nDetails."
    )

    result = format_rule_description("Making an Attack", source)

    assert result == "Intro text.\n\n**Modifiers to the Roll**\n\nDetails."


def test_condition_description_lists_are_normalized():
    assert description_text(["First effect.", "Second effect."]) == (
        "First effect.\n\nSecond effect."
    )


def test_condition_embed_identifies_its_reference_type():
    entry = ReferenceEntry(
        "restrained",
        "Restrained",
        "/conditions/restrained",
        CONDITION,
    )

    embed = reference_embeds(
        entry,
        {
            "name": "Restrained",
            "desc": ["Speed becomes 0.", "Attacks have disadvantage."],
        },
    )[0]

    assert embed.title == "Restrained — Condition"
    assert embed.url is None
    assert "Speed becomes 0." in embed.description
    assert "Condition" in embed.footer.text


def test_reference_embed_omits_source_link_when_url_is_missing():
    entry = ReferenceEntry("restrained", "Restrained", "", CONDITION)

    embed = reference_embeds(entry, {"name": "Restrained", "desc": ["Text."]})[0]

    assert embed.url is None


def test_reference_formatter_handles_list_markdown():
    result = format_reference_description(
        "Restrained",
        ["# Restrained", "#### Effects", "Speed becomes 0."],
    )

    assert result == "**Effects**\n\nSpeed becomes 0."


def test_reference_formatter_translates_markdown_tables_to_labeled_bullets():
    source = """##### Travel Pace

| Pace | Distance per: Minute | Hour | Day | Effect |
|------|----------------------|------|-----|--------|
| Fast | 400 feet | 4 miles | 30 miles | -5 passive Perception |
| Normal | 300 feet | 3 miles | 24 miles | - |
"""

    result = format_reference_description("Movement", source)

    assert "| Pace |" not in result
    assert "**Travel Pace**" in result
    assert (
        """**Fast**
> **Distance per Minute:** 400 feet
> **Hour:** 4 miles
> **Day:** 30 miles
> **Effect:** -5 passive Perception"""
        in result
    )
    assert (
        """**Normal**
> **Distance per Minute:** 300 feet
> **Hour:** 3 miles
> **Day:** 24 miles"""
        in result
    )


def test_search_results_are_grouped_five_per_page():
    results = [
        SearchResult(
            ReferenceEntry(
                f"rule-{number}",
                f"Rule {number}",
                f"/rule-sections/rule-{number}",
                RULE,
            ),
            score=100 - number,
            excerpt="A matching excerpt.",
        )
        for number in range(7)
    ]

    embeds = search_result_embeds("matching", results)

    assert len(embeds) == 2
    assert len(embeds[0].fields) == 5
    assert len(embeds[1].fields) == 2
    assert embeds[0].fields[0].name == "1. Rule 0 — Rule"
    assert embeds[1].fields[0].name == "6. Rule 5 — Rule"


def test_reference_list_filters_and_sorts_results():
    entries = [
        ReferenceEntry("restrained", "Restrained", "/conditions/restrained", CONDITION),
        ReferenceEntry("cover", "Cover", "/rule-sections/cover", RULE),
        ReferenceEntry("invisible", "Invisible", "/conditions/invisible", CONDITION),
    ]

    results = reference_list_results(entries, "conditions")
    embeds = reference_list_embeds("conditions", results)

    assert [result.entry.name for result in results] == ["Invisible", "Restrained"]
    assert embeds[0].title == "SRD references — Conditions"
    assert embeds[0].fields[0].name == "1. Invisible — Condition"


def test_reference_list_rejects_invalid_topics():
    with pytest.raises(ValueError, match="all, rules, or conditions"):
        reference_list_results([], "spells")
