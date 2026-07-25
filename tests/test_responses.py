from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from rubberneck.cogs.responses import ResponseSession


@pytest.fixture
def ctx():
    return SimpleNamespace(defer=AsyncMock(), respond=AsyncMock())


@pytest.mark.asyncio
@pytest.mark.parametrize("private", [False, True])
async def test_defer_uses_selected_visibility(ctx, private):
    await ResponseSession(ctx, private).defer()

    ctx.defer.assert_awaited_once_with(ephemeral=private)


@pytest.mark.asyncio
async def test_success_uses_selected_visibility(ctx):
    await ResponseSession(ctx, True).send("Result")

    ctx.respond.assert_awaited_once_with("Result", ephemeral=True)


@pytest.mark.asyncio
async def test_errors_are_private_even_for_public_commands(ctx):
    await ResponseSession(ctx, False).send("No result", error=True)

    ctx.respond.assert_awaited_once_with("No result", ephemeral=True)
