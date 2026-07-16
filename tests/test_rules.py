from cogs.rules import (
    RULE_PAGE_DESCRIPTION_LIMIT,
    Rules,
    _build_autocomplete_index,
    format_rule_description,
    split_description,
)


class TestRuleFormatting:
    def test_short_description_is_unchanged(self):
        assert split_description("Short rule.") == ["Short rule."]

    def test_long_description_respects_embed_limit(self):
        chunks = split_description(("A useful sentence. " * 500).strip(), limit=200)
        assert len(chunks) > 1
        assert all(len(chunk) <= 200 for chunk in chunks)

    def test_empty_description_has_fallback(self):
        assert split_description("") == ["No description is available for this rule."]

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


def test_rule_markdown_removes_duplicate_title_and_formats_headings():
    source = "# Making an Attack\n\nIntro text.\n\n#### Modifiers to the Roll\n\nDetails."

    result = format_rule_description("Making an Attack", source)

    assert result == "Intro text.\n\n**Modifiers to the Roll**\n\nDetails."


def test_autocomplete_index_supports_infix_search_without_runtime_filtering():
    from service.api_client import ResourceReference

    rules = [
        ResourceReference("making-an-attack", "Making an Attack", "/rules/making-an-attack"),
        ResourceReference("cover", "Cover", "/rules/cover"),
    ]

    index = _build_autocomplete_index(rules)

    assert [choice.value for choice in index["attack"]] == ["making-an-attack"]
    assert [choice.value for choice in index["cov"]] == ["cover"]
