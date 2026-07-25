from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import cogs.bestiary as bestiary_module
from cogs.bestiary import (
    MONSTER,
    MONSTER_NOT_FOUND_MESSAGE,
    MONSTERS_NOT_READY_MESSAGE,
    Bestiary,
    chunk_entries,
    monster_embed,
    monster_list_embeds,
)
from service.api_client import DnDAPIError, ResourceNotFound
from service.reference_catalog import AutocompleteMetrics, ReferenceEntry


def monster_entry(number: int = 1) -> ReferenceEntry:
    return ReferenceEntry(
        f"monster-{number}",
        f"Monster {number}",
        f"/monsters/monster-{number}",
        MONSTER,
    )


@pytest.fixture
def ctx():
    return SimpleNamespace(
        defer=AsyncMock(),
        respond=AsyncMock(),
        interaction=object(),
    )


@pytest.fixture
def cog():
    result = Bestiary(bot=object(), client=object())
    result.catalog = SimpleNamespace(
        entries=[],
        load=AsyncMock(),
        choices=MagicMock(return_value=[]),
        resolve=AsyncMock(),
        autocomplete_metrics=AutocompleteMetrics(1.0, 10, 20),
    )
    return result


def test_chunk_entries_rejects_invalid_page_size():
    with pytest.raises(ValueError):
        chunk_entries([monster_entry()], 0)


def test_monster_list_embeds_sort_and_paginate_entries():
    entries = [monster_entry(number) for number in range(21, 0, -1)]

    embeds = monster_list_embeds(entries)

    assert len(embeds) == 2
    assert embeds[0].title == "SRD Monsters (1/2)"
    assert embeds[0].description.startswith("• Monster 1\n")
    assert "21 monsters" in embeds[0].footer.text


def test_monster_embed_formats_core_statistics_and_actions():
    embed = monster_embed(
        {
            "name": "Owlbear",
            "size": "Large",
            "type": "monstrosity",
            "alignment": "unaligned",
            "armor_class": [{"type": "natural", "value": 13}],
            "hit_points": 59,
            "speed": {"walk": "40 ft."},
            "strength": 20,
            "dexterity": 12,
            "constitution": 17,
            "intelligence": 3,
            "wisdom": 12,
            "charisma": 7,
            "challenge_rating": 3,
            "xp": 700,
            "languages": "",
            "actions": [{"name": "Beak", "desc": "Melee Weapon Attack."}],
        }
    )

    assert embed.title == "Owlbear"
    assert embed.description == "Large monstrosity, unaligned"
    assert any(
        field.name == "Armor Class" and field.value == "13" for field in embed.fields
    )
    assert any(
        field.name == "Actions" and "Beak" in field.value for field in embed.fields
    )


@pytest.mark.asyncio
async def test_load_monsters_retries_transient_api_failure(cog, monkeypatch):
    cog.catalog.load.side_effect = [DnDAPIError("offline"), None]
    sleep = AsyncMock()
    monkeypatch.setattr(bestiary_module.asyncio, "sleep", sleep)

    await cog.load_monsters()

    assert cog.catalog.load.await_count == 2
    sleep.assert_awaited_once_with(bestiary_module.MONSTER_RETRY_DELAY_SECONDS)


@pytest.mark.asyncio
async def test_monster_autocomplete_uses_precomputed_catalog(cog):
    cog.catalog.choices.return_value = ["owlbear"]

    result = await cog.monster_autocomplete(SimpleNamespace(value="owl"))

    assert result == ["owlbear"]
    cog.catalog.choices.assert_called_once_with("owl", MONSTER)


@pytest.mark.asyncio
async def test_monsters_reports_catalog_startup_failure(cog, ctx):
    await cog.monsters.callback(cog, ctx)

    ctx.defer.assert_awaited_once_with()
    ctx.respond.assert_awaited_once_with(
        MONSTERS_NOT_READY_MESSAGE,
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_monster_returns_formatted_embed(cog, ctx):
    cog.catalog.resolve.return_value = (
        monster_entry(),
        {"name": "Owlbear", "armor_class": [], "speed": {}},
    )

    await cog.monster.callback(cog, ctx, "monster:owlbear")

    response = ctx.respond.await_args.kwargs
    assert response["embed"].title == "Owlbear"


@pytest.mark.asyncio
async def test_monster_reports_missing_resource(cog, ctx):
    cog.catalog.resolve.side_effect = ResourceNotFound("missing")

    await cog.monster.callback(cog, ctx, "missing")

    ctx.respond.assert_awaited_with(MONSTER_NOT_FOUND_MESSAGE, ephemeral=True)
