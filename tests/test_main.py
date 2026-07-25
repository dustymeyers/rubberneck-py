import importlib
from unittest.mock import MagicMock

from discord.ext import commands


def test_import_does_not_start_bot_and_demo_cog_is_excluded(monkeypatch):
    run = MagicMock()
    monkeypatch.setattr(commands.Bot, "run", run)

    main = importlib.import_module("main")

    run.assert_not_called()
    assert main.PRODUCTION_COGS == ("bestiary", "rules")


def test_production_cog_loader_uses_only_configured_extensions():
    main = importlib.import_module("main")
    bot = MagicMock()

    main.load_production_cogs(bot)

    assert bot.load_extension.call_args_list == [
        (("rubberneck.cogs.bestiary",), {}),
        (("rubberneck.cogs.rules",), {}),
    ]
