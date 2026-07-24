from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import cogs.rules as rules_module
from cogs.rules import (
    NO_SEARCH_RESULTS_MESSAGE,
    REFERENCE_NOT_FOUND_MESSAGE,
    RULE_NOT_FOUND_MESSAGE,
    SEARCH_NOT_READY_MESSAGE,
    Rules,
)
from service.api_client import DnDAPIError, ResourceNotFound
from service.reference_catalog import RULE, ReferenceEntry
from service.reference_search import InvalidSearchQuery, SearchResult


@pytest.fixture
def ctx():
    return SimpleNamespace(
        defer=AsyncMock(),
        respond=AsyncMock(),
        interaction=object(),
    )


@pytest.fixture
def cog():
    result = Rules(bot=object(), client=object())
    result.catalog = SimpleNamespace(
        entries=[],
        load=AsyncMock(),
        choices=MagicMock(return_value=[]),
        resolve=AsyncMock(),
    )
    result.search_index = SimpleNamespace(
        documents=(),
        load=AsyncMock(),
        search=MagicMock(return_value=[]),
    )
    return result


def search_result(number=1):
    entry = ReferenceEntry(
        f"rule-{number}",
        f"Rule {number}",
        f"/rule-sections/rule-{number}",
        RULE,
    )
    return SearchResult(entry, score=100 - number, excerpt="Matching text.")


@pytest.mark.asyncio
async def test_load_references_builds_catalog_and_search_index(cog):
    cog.catalog.entries = [search_result().entry]

    await cog.load_references()

    cog.catalog.load.assert_awaited_once_with()
    cog.search_index.load.assert_awaited_once_with(cog.catalog.entries)


@pytest.mark.asyncio
async def test_load_references_logs_api_failure_without_raising(cog, monkeypatch):
    cog.catalog.load.side_effect = DnDAPIError("offline")
    exception = MagicMock()
    monkeypatch.setattr(rules_module.logger, "exception", exception)

    await cog.load_references()

    exception.assert_called_once_with("Could not preload SRD references")
    cog.search_index.load.assert_not_awaited()


@pytest.mark.asyncio
async def test_on_ready_loads_only_when_an_index_is_missing(cog):
    cog.load_references = AsyncMock()

    await cog.on_ready()
    cog.load_references.assert_awaited_once_with()

    cog.load_references.reset_mock()
    cog.catalog.entries = [search_result().entry]
    cog.search_index.documents = (object(),)
    await cog.on_ready()
    cog.load_references.assert_not_awaited()


@pytest.mark.asyncio
async def test_autocomplete_delegates_to_precomputed_catalog(cog):
    cog.catalog.choices.side_effect = [["all"], ["rules"]]

    all_choices = await cog.reference_autocomplete(SimpleNamespace(value="cov"))
    rule_choices = await cog.rule_autocomplete(SimpleNamespace(value=None))

    assert all_choices == ["all"]
    assert rule_choices == ["rules"]
    assert cog.catalog.choices.call_args_list[0].args == ("cov",)
    assert cog.catalog.choices.call_args_list[1].args == ("", RULE)


@pytest.mark.asyncio
async def test_lookup_and_legacy_rule_delegate_with_correct_scope(cog, ctx):
    cog._respond_with_reference = AsyncMock()

    await Rules.lookup.callback(cog, ctx, "cover")
    await Rules.rule.callback(cog, ctx, "cover")

    assert cog._respond_with_reference.await_args_list[0].args == (ctx, "cover")
    assert cog._respond_with_reference.await_args_list[1].args == (
        ctx,
        "cover",
        RULE,
    )
    assert cog._respond_with_reference.await_args_list[1].kwargs == {
        "legacy_alias": True
    }


@pytest.mark.asyncio
async def test_search_reports_index_not_ready(cog, ctx):
    await Rules.search.callback(cog, ctx, "hidden")

    ctx.defer.assert_awaited_once_with()
    ctx.respond.assert_awaited_once_with(SEARCH_NOT_READY_MESSAGE, ephemeral=True)


@pytest.mark.asyncio
async def test_search_reports_invalid_and_no_result_queries(cog, ctx):
    cog.search_index.documents = (object(),)
    cog.search_index.search.side_effect = InvalidSearchQuery("too short")

    await Rules.search.callback(cog, ctx, "a")
    ctx.respond.assert_awaited_once_with("too short", ephemeral=True)

    ctx.respond.reset_mock()
    cog.search_index.search.side_effect = None
    cog.search_index.search.return_value = []
    await Rules.search.callback(cog, ctx, "xyzzy")
    ctx.respond.assert_awaited_once_with(NO_SEARCH_RESULTS_MESSAGE, ephemeral=True)


@pytest.mark.asyncio
async def test_search_responds_with_one_embed(cog, ctx):
    cog.search_index.documents = (object(),)
    cog.search_index.search.return_value = [search_result()]

    await Rules.search.callback(cog, ctx, "matching")

    response = ctx.respond.await_args.kwargs
    assert response["embed"].fields[0].value == "Matching text."


@pytest.mark.asyncio
async def test_search_uses_one_paginator_for_multiple_pages(cog, ctx, monkeypatch):
    cog.search_index.documents = (object(),)
    cog.search_index.search.return_value = [
        search_result(number) for number in range(6)
    ]
    paginator = SimpleNamespace(respond=AsyncMock())
    paginator_class = MagicMock(return_value=paginator)
    monkeypatch.setattr(rules_module, "Paginator", paginator_class)

    await Rules.search.callback(cog, ctx, "matching")

    assert len(paginator_class.call_args.kwargs["pages"]) == 2
    await_args = paginator.respond.await_args
    assert await_args.args == (ctx.interaction,)
    assert await_args.kwargs == {"ephemeral": False}


@pytest.mark.asyncio
async def test_reference_response_handles_single_and_paginated_results(
    cog,
    ctx,
    monkeypatch,
):
    entry = search_result().entry
    cog.catalog.resolve.return_value = (entry, {"name": "Rule 1", "desc": "Short."})

    await cog._respond_with_reference(ctx, "rule-1")
    assert ctx.respond.await_args.kwargs["embed"].description == "Short."

    ctx.respond.reset_mock()
    long_description = ("Long sentence. " * 300).strip()
    cog.catalog.resolve.return_value = (
        entry,
        {"name": "Rule 1", "desc": long_description},
    )
    paginator = SimpleNamespace(respond=AsyncMock())
    paginator_class = MagicMock(return_value=paginator)
    monkeypatch.setattr(rules_module, "Paginator", paginator_class)

    await cog._respond_with_reference(ctx, "rule-1")

    assert len(paginator_class.call_args.kwargs["pages"]) > 1
    paginator.respond.assert_awaited_once_with(ctx.interaction, ephemeral=False)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("reference_type", "expected"),
    [(None, REFERENCE_NOT_FOUND_MESSAGE), (RULE, RULE_NOT_FOUND_MESSAGE)],
)
async def test_reference_response_reports_missing_resource(
    cog,
    ctx,
    reference_type,
    expected,
):
    cog.catalog.resolve.side_effect = ResourceNotFound("missing")

    await cog._respond_with_reference(ctx, "missing", reference_type)

    ctx.respond.assert_awaited_once_with(expected, ephemeral=True)


@pytest.mark.asyncio
async def test_reference_response_reports_api_failure(cog, ctx, monkeypatch):
    cog.catalog.resolve.side_effect = DnDAPIError("temporarily unavailable")
    error = MagicMock()
    monkeypatch.setattr(rules_module.logger, "error", error)

    await cog._respond_with_reference(ctx, "cover")

    error.assert_called_once()
    ctx.respond.assert_awaited_once_with("temporarily unavailable", ephemeral=True)


def test_setup_adds_rules_cog():
    bot = SimpleNamespace(add_cog=MagicMock())

    rules_module.setup(bot)

    added = bot.add_cog.call_args.args[0]
    assert isinstance(added, Rules)
    assert added.bot is bot
