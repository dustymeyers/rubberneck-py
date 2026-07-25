import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from rubberneck.logging import logger

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

PRODUCTION_COGS = (
    "bestiary",
    "rules",
)

# bot: Bot = Rubberneck(intents=discord.Intents.all())

bot = commands.Bot(intents=discord.Intents.all())


@bot.slash_command()
async def ping(ctx):
    await ctx.respond("Pong!")


@bot.event
async def on_ready():
    logger.info("Logged in as %s", bot.user)


@bot.event
async def on_application_command_error(ctx, error):
    """Log command failures and ensure Discord receives a response."""
    original = getattr(error, "original", error)
    logger.error(
        "Application command /%s failed: %s",
        getattr(ctx.command, "qualified_name", "unknown"),
        original,
        exc_info=(type(original), original, original.__traceback__),
    )

    message = (
        "Something went wrong while running that command. The error has been logged."
    )
    try:
        if ctx.interaction.response.is_done():
            await ctx.send_followup(message, ephemeral=True)
        else:
            await ctx.respond(message, ephemeral=True)
    except discord.HTTPException:
        logger.exception("Could not send the command error response to Discord")


def load_production_cogs(target_bot):
    """Load only cogs intended to register commands in normal deployments."""
    for extension in PRODUCTION_COGS:
        target_bot.load_extension(f"rubberneck.cogs.{extension}")


def main() -> None:
    """Load production extensions and connect the bot to Discord."""
    load_production_cogs(bot)
    bot.run(TOKEN)
