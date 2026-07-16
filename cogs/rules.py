"""Slash commands for looking up rules in the D&D 5e SRD."""

from typing import Any
import re

import discord
from discord.ext import commands
from discord.ext.pages import Paginator

from logger import logger
from service.api_client import DnDAPI, DnDAPIError, ResourceNotFound, ResourceReference


RULE_SECTIONS_ENDPOINT = "rule-sections"
RULE_COMMAND_DESCRIPTION = "Look up a rule in the D&D 5e SRD."
RULE_OPTION_DESCRIPTION = "Rule name, such as 'Cover' or 'Making an Attack'"
RULE_NOT_FOUND_MESSAGE = (
    "I couldn't find that SRD rule. Start typing the name and choose a suggestion."
)
RULE_FOOTER = "D&D 5e SRD (2014) - dnd5eapi.co"
DEFAULT_RULE_NAME = "SRD Rule"
EMPTY_RULE_DESCRIPTION = "No description is available for this rule."
# Sized for comfortable reading in a typical Discord desktop viewport rather
# than Discord's much larger technical embed limit.
RULE_PAGE_DESCRIPTION_LIMIT = 1400
MAX_RULE_PAGES = 20
PAGINATOR_TIMEOUT_SECONDS = 300
DISCORD_AUTOCOMPLETE_LIMIT = 25


def format_rule_description(name: str, text: str) -> str:
    """Translate SRD Markdown into the subset Discord embeds render cleanly."""
    text = text.replace("\r\n", "\n").strip()
    lines = text.splitlines()

    # API descriptions often repeat the resource name as their first heading.
    if lines and lines[0].lstrip("# ").strip().casefold() == name.strip().casefold():
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines.pop(0)

    formatted: list[str] = []
    for line in lines:
        heading = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
        formatted.append(f"**{heading.group(1)}**" if heading else line)
    return "\n".join(formatted).strip()


def split_description(text: str, limit: int = RULE_PAGE_DESCRIPTION_LIMIT) -> list[str]:
    """Build readable pages while keeping headings with their first paragraph."""
    text = text.strip()
    if not text:
        return [EMPTY_RULE_DESCRIPTION]

    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    units: list[str] = []
    index = 0
    while index < len(blocks):
        block = blocks[index]
        if _is_heading(block) and index + 1 < len(blocks):
            units.append(f"{block}\n\n{blocks[index + 1]}")
            index += 2
        else:
            units.append(block)
            index += 1

    pages: list[str] = []
    current = ""
    for unit in units:
        for piece in _split_oversized_unit(unit, limit):
            candidate = f"{current}\n\n{piece}" if current else piece
            if len(candidate) <= limit:
                current = candidate
            else:
                if current:
                    pages.append(current)
                current = piece
    if current:
        pages.append(current)
    return pages


def _is_heading(block: str) -> bool:
    return block.startswith("**") and block.endswith("**") and "\n" not in block


def _split_oversized_unit(unit: str, limit: int) -> list[str]:
    """Split only when a structural unit cannot fit on one page."""
    if len(unit) <= limit:
        return [unit]

    pieces: list[str] = []
    remaining = unit
    while len(remaining) > limit:
        split_at = remaining.rfind(". ", 0, limit + 1)
        if split_at >= limit // 2:
            split_at += 1
        else:
            split_at = remaining.rfind(" ", 0, limit + 1)
        if split_at < limit // 2:
            split_at = limit
        pieces.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        pieces.append(remaining)
    return pieces


def rule_embeds(rule: dict[str, Any]) -> list[discord.Embed]:
    name = rule.get("name", DEFAULT_RULE_NAME)
    descriptions = split_description(format_rule_description(name, rule.get("desc", "")))
    embeds: list[discord.Embed] = []
    for number, description in enumerate(descriptions, start=1):
        title = name if len(descriptions) == 1 else f"{name} ({number}/{len(descriptions)})"
        embed = discord.Embed(title=title, description=description, color=discord.Colour.blurple())
        embed.set_footer(text=RULE_FOOTER)
        embeds.append(embed)
    return embeds[:MAX_RULE_PAGES]


class Rules(commands.Cog):
    def __init__(self, bot: commands.Bot, client: DnDAPI | None = None):
        self.bot = bot
        self.client = client or DnDAPI()
        self.rules: list[ResourceReference] = []
        self.autocomplete_index: dict[str, tuple[discord.OptionChoice, ...]] = {}

    async def load_rules(self) -> None:
        try:
            self.rules = await self.client.list_resources(RULE_SECTIONS_ENDPOINT)
            self.autocomplete_index = _build_autocomplete_index(self.rules)
            logger.info("Loaded %s SRD rule names for autocomplete", len(self.rules))
        except DnDAPIError:
            logger.exception("Could not preload SRD rule names")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.rules:
            await self.load_rules()

    async def rule_autocomplete(self, ctx: discord.AutocompleteContext) -> list[discord.OptionChoice]:
        query = (ctx.value or "").strip().casefold()
        return list(self.autocomplete_index.get(query, ()))

    @discord.slash_command(name="rule", description=RULE_COMMAND_DESCRIPTION)
    async def rule(
        self,
        ctx: discord.ApplicationContext,
        name: discord.Option(
            str,
            RULE_OPTION_DESCRIPTION,
            autocomplete=rule_autocomplete,
        ),
    ) -> None:
        await ctx.defer()
        try:
            rule = await self.client.get_resource(RULE_SECTIONS_ENDPOINT, name)
            embeds = rule_embeds(rule)
            if len(embeds) == 1:
                await ctx.respond(embed=embeds[0])
            else:
                paginator = Paginator(
                    pages=embeds,
                    show_disabled=False,
                    timeout=PAGINATOR_TIMEOUT_SECONDS,
                )
                await paginator.respond(ctx.interaction, ephemeral=False)
        except ResourceNotFound:
            await ctx.respond(RULE_NOT_FOUND_MESSAGE, ephemeral=True)
        except DnDAPIError as exc:
            logger.error("Rule lookup failed: %s", exc, exc_info=True)
            await ctx.respond(str(exc), ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Rules(bot))


def _build_autocomplete_index(
    rules: list[ResourceReference],
) -> dict[str, tuple[discord.OptionChoice, ...]]:
    """Precompute every substring lookup used by Discord autocomplete."""
    choices = {
        rule.index: discord.OptionChoice(name=rule.name, value=rule.index)
        for rule in rules
    }
    matches: dict[str, list[discord.OptionChoice]] = {"": list(choices.values())}

    for rule in rules:
        searchable = {rule.name.casefold(), rule.index.casefold()}
        queries = {
            value[start:end]
            for value in searchable
            for start in range(len(value))
            for end in range(start + 1, len(value) + 1)
        }
        for query in queries:
            bucket = matches.setdefault(query, [])
            if len(bucket) < DISCORD_AUTOCOMPLETE_LIMIT:
                bucket.append(choices[rule.index])

    return {
        query: tuple(results[:DISCORD_AUTOCOMPLETE_LIMIT])
        for query, results in matches.items()
    }
