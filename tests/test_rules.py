from cogs.rules import (
    EMPTY_REFERENCE_DESCRIPTION,
    RULE_PAGE_DESCRIPTION_LIMIT,
    Rules,
    description_text,
    format_reference_description,
    format_rule_description,
    reference_embeds,
    split_description,
)
from service.reference_catalog import CONDITION, ReferenceEntry


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


def test_rules_group_registers_only_unified_lookup():
    commands = {command.name: command for command in Rules.rules.subcommands}

    assert set(commands) == {"lookup"}
    lookup_option = next(
        option for option in commands["lookup"].options if option.name == "term"
    )
    assert lookup_option._raw_type is str
    assert lookup_option.autocomplete is Rules.reference_autocomplete


def test_rule_markdown_removes_duplicate_title_and_formats_headings():
    source = "# Making an Attack\n\nIntro text.\n\n#### Modifiers to the Roll\n\nDetails."

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
        {"name": "Restrained", "desc": ["Speed becomes 0.", "Attacks have disadvantage."]},
    )[0]

    assert embed.title == "Restrained — Condition"
    assert "Speed becomes 0." in embed.description
    assert "Condition" in embed.footer.text


def test_reference_formatter_handles_list_markdown():
    result = format_reference_description(
        "Restrained",
        ["# Restrained", "#### Effects", "Speed becomes 0."],
    )

    assert result == "**Effects**\n\nSpeed becomes 0."
