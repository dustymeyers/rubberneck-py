import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest
import pytest_asyncio

from cogs.reference_navigation import (
    MISSING_INDEXED_REFERENCE_MESSAGE,
    NAVIGATION_OWNER_MESSAGE,
    ReferenceNavigatorView,
)
from service.reference_catalog import RULE, ReferenceEntry
from service.reference_search import SearchResult


def result(number):
    entry = ReferenceEntry(
        f"rule-{number}",
        f"Rule {number}",
        f"/rule-sections/rule-{number}",
        RULE,
    )
    return SearchResult(entry, 100 - number, f"Excerpt {number}")


def embed(title):
    return discord.Embed(title=title, description=f"{title} description")


def interaction(user_id=42):
    return SimpleNamespace(
        user=SimpleNamespace(id=user_id),
        response=SimpleNamespace(
            edit_message=AsyncMock(),
            send_message=AsyncMock(),
        ),
    )


@pytest_asyncio.fixture
async def view():
    results = [result(number) for number in range(6)]

    def payload_for(entry):
        return {"name": entry.name, "desc": "Full reference text."}

    def reference_pages(entry, payload):
        return [embed(f"{entry.name} page 1"), embed(f"{entry.name} page 2")]

    def related_for(entry):
        if entry.value == results[0].entry.value:
            return [results[1].entry]
        if entry.value == results[1].entry.value:
            return [results[0].entry]
        return []

    return ReferenceNavigatorView(
        owner_id=42,
        query="rule",
        results=results,
        search_pages=[embed("Search 1"), embed("Search 2")],
        payload_for=payload_for,
        reference_pages=reference_pages,
        related_for=related_for,
        results_per_page=5,
        timeout=300,
    )


@pytest.mark.asyncio
async def test_search_page_controls_update_options_and_restore_page(view):
    source = interaction()
    await view.next_button.callback(source)

    assert view.search_page == 1
    assert [button.label for button in view.result_buttons] == [
        "6",
        "—",
        "—",
        "—",
        "—",
    ]
    assert [button.disabled for button in view.result_buttons] == [
        False,
        True,
        True,
        True,
        True,
    ]

    await view.result_buttons[0].callback(source)
    assert view.mode == "reference"
    assert view.current_embed.title == "Rule 5 page 1"

    await view.back_button.callback(source)
    assert view.mode == "search"
    assert view.search_page == 1
    assert view.current_embed.title == "Search 2"


@pytest.mark.asyncio
async def test_reference_page_controls_reuse_same_message(view):
    source = interaction()

    await view.result_buttons[0].callback(source)
    await view.next_button.callback(source)

    assert view.reference_page == 1
    assert view.current_embed.title == "Rule 0 page 2"
    assert source.response.edit_message.await_count == 2
    assert all(
        call.kwargs["view"] is view
        for call in source.response.edit_message.await_args_list
    )


@pytest.mark.asyncio
async def test_back_and_forward_restore_exact_reference_page(view):
    source = interaction()

    await view.result_buttons[0].callback(source)
    await view.next_button.callback(source)
    await view.back_button.callback(source)

    assert view.mode == "search"
    assert view.forward_button.disabled is False

    await view.forward_button.callback(source)

    assert view.mode == "reference"
    assert view.reference_entry.index == "rule-0"
    assert view.reference_page == 1
    assert view.current_embed.title == "Rule 0 page 2"


@pytest.mark.asyncio
async def test_new_navigation_after_back_clears_forward_history(view):
    source = interaction()

    await view.result_buttons[0].callback(source)
    await view.back_button.callback(source)
    await view.next_button.callback(source)

    assert view.mode == "search"
    assert view.search_page == 1
    assert not view.forward_history
    assert view.forward_button.disabled is True


@pytest.mark.asyncio
async def test_related_reference_uses_history_and_back_restores_source(view):
    source = interaction()
    await view.result_buttons[0].callback(source)

    assert [option.value for option in view.related_select.options] == [
        "rule:rule-1"
    ]
    view.related_select._interaction = source
    view.related_select._selected_values = ["rule:rule-1"]
    await view.related_select.callback(source)

    assert view.reference_entry.index == "rule-1"
    assert view.current_embed.title == "Rule 1 page 1"

    await view.back_button.callback(source)
    assert view.reference_entry.index == "rule-0"
    assert view.current_embed.title == "Rule 0 page 1"


@pytest.mark.asyncio
async def test_missing_related_payload_preserves_current_reference(view):
    source = interaction()
    await view.result_buttons[0].callback(source)
    original_payload_for = view.payload_for
    view.payload_for = lambda entry: (
        (_ for _ in ()).throw(KeyError(entry.value))
        if entry.index == "rule-1"
        else original_payload_for(entry)
    )
    view.related_select._interaction = source
    view.related_select._selected_values = ["rule:rule-1"]

    await view.related_select.callback(source)

    assert view.reference_entry.index == "rule-0"
    source.response.send_message.assert_awaited_once_with(
        MISSING_INDEXED_REFERENCE_MESSAGE,
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_concurrent_result_clicks_only_open_one_reference(view):
    first = interaction()
    second = interaction()

    await asyncio.gather(
        view.result_buttons[0].callback(first),
        view.result_buttons[1].callback(second),
    )

    assert view.mode == "reference"
    assert (
        first.response.edit_message.await_count
        + second.response.edit_message.await_count
        == 1
    )
    assert (
        first.response.send_message.await_count
        + second.response.send_message.await_count
        == 1
    )


@pytest.mark.asyncio
async def test_timeout_disables_all_controls(view):
    message = SimpleNamespace(
        flags=SimpleNamespace(ephemeral=False),
        edit=AsyncMock(),
    )
    view._message = message

    await view.on_timeout()

    assert all(item.disabled for item in view.children)
    message.edit.assert_awaited_once_with(view=view)


@pytest.mark.asyncio
async def test_navigation_rejects_other_users_privately(view):
    source = interaction(user_id=99)

    assert await view.interaction_check(source) is False
    await view.on_check_failure(source)

    source.response.send_message.assert_awaited_once_with(
        NAVIGATION_OWNER_MESSAGE,
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_missing_indexed_reference_does_not_change_state(view):
    source = interaction()
    view.payload_for = lambda entry: (_ for _ in ()).throw(KeyError(entry.value))

    await view.result_buttons[0].callback(source)

    assert view.mode == "search"
    assert not view.history
    source.response.send_message.assert_awaited_once_with(
        MISSING_INDEXED_REFERENCE_MESSAGE,
        ephemeral=True,
    )


def test_component_layout_stays_within_discord_limits(view):
    components = view.to_components()

    assert len(view.children) == 11
    assert len(components) == 3
    assert len(view.result_buttons) == 5


@pytest.mark.asyncio
async def test_navigator_can_start_as_direct_reference_without_search_buttons():
    source_entry = result(0).entry
    related_entry = result(1).entry
    view = ReferenceNavigatorView(
        owner_id=42,
        query="",
        results=[],
        search_pages=[],
        payload_for=lambda entry: {"name": entry.name, "desc": "Full text."},
        reference_pages=lambda entry, payload: [embed(entry.name)],
        related_for=lambda entry: [related_entry] if entry == source_entry else [],
        results_per_page=5,
        timeout=300,
        initial_reference=source_entry,
        initial_reference_pages=[embed(source_entry.name)],
    )

    assert view.mode == "reference"
    assert not view.result_buttons
    assert view.related_select.disabled is False
    assert view.current_embed.title == source_entry.name
