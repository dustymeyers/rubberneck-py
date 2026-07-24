"""Slash commands for looking up D&D 5e SRD reference material."""

import os
import re
from typing import Annotated, Any

import discord
from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord.ext.pages import Paginator
from dotenv import load_dotenv

from logger import logger
from service.api_client import DnDAPI, DnDAPIError, ResourceNotFound
from service.reference_catalog import (
    RULE,
    ReferenceCatalog,
    ReferenceEntry,
    ReferenceType,
)
from service.reference_search import (
    InvalidSearchQuery,
    ReferenceSearchIndex,
    SearchResult,
)


RULES_GROUP_DESCRIPTION = "Look up rules, conditions, and other SRD references."
LOOKUP_COMMAND_DESCRIPTION = "Look up a rule or condition in the D&D 5e SRD."
SEARCH_COMMAND_DESCRIPTION = "Search inside SRD rule and condition descriptions."
RULE_COMMAND_DESCRIPTION = "Look up a rule section in the D&D 5e SRD."
REFERENCE_OPTION_DESCRIPTION = "Reference name, such as 'Cover' or 'Restrained'"
SEARCH_OPTION_DESCRIPTION = "Words or a phrase, such as 'attack while hidden'"
RULE_OPTION_DESCRIPTION = "Rule name, such as 'Cover' or 'Making an Attack'"
REFERENCE_NOT_FOUND_MESSAGE = (
    "I couldn't find that SRD reference. Start typing the name and choose a suggestion."
)
RULE_NOT_FOUND_MESSAGE = (
    "I couldn't find that SRD rule. Start typing the name and choose a suggestion."
)
SEARCH_NOT_READY_MESSAGE = "The local SRD search index is not ready yet. Try again shortly."
NO_SEARCH_RESULTS_MESSAGE = (
    "I couldn't find that text in the indexed SRD references. "
    "Try fewer or more specific words."
)
SRD_NAME = "D&D 5e SRD (2014)"
SOURCE_NAME = "dnd5eapi.co"
LEGACY_RULE_HINT = "Tip: /rules lookup also searches conditions."
DEFAULT_REFERENCE_NAME = "SRD Reference"
EMPTY_REFERENCE_DESCRIPTION = "No description is available for this reference."
RULE_PAGE_DESCRIPTION_LIMIT = 1400
MAX_REFERENCE_PAGES = 20
PAGINATOR_TIMEOUT_SECONDS = 300
SEARCH_RESULTS_PER_PAGE = 5


load_dotenv()
CONFIGURED_GUILD_ID = os.getenv("GUILD_ID")
COMMAND_GUILD_IDS = [int(CONFIGURED_GUILD_ID)] if CONFIGURED_GUILD_ID else None


def description_text(value: str | list[str] | None) -> str:
    """Normalize API description shapes into one Markdown string."""
    if isinstance(value, list):
        return "\n\n".join(part.strip() for part in value if part.strip())
    return value or ""


def format_reference_description(name: str, value: str | list[str] | None) -> str:
    """Translate SRD Markdown into the subset Discord embeds render cleanly."""
    text = description_text(value).replace("\r\n", "\n").strip()
    lines = text.splitlines()

    if lines and lines[0].lstrip("# ").strip().casefold() == name.strip().casefold():
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines.pop(0)

    formatted: list[str] = []
    for line in lines:
        heading = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
        formatted.append(f"**{heading.group(1)}**" if heading else line)
    return "\n".join(formatted).strip()


def format_rule_description(name: str, text: str) -> str:
    """Compatibility wrapper for callers of the original rule formatter."""
    return format_reference_description(name, text)


def split_description(text: str, limit: int = RULE_PAGE_DESCRIPTION_LIMIT) -> list[str]:
    """Build readable pages while keeping headings with their first paragraph."""
    text = text.strip()
    if not text:
        return [EMPTY_REFERENCE_DESCRIPTION]

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


def reference_embeds(
    entry: ReferenceEntry,
    payload: dict[str, Any],
    legacy_alias: bool = False,
) -> list[discord.Embed]:
    name = payload.get("name", entry.name or DEFAULT_REFERENCE_NAME)
    text = format_reference_description(name, payload.get("desc"))
    descriptions = split_description(text)
    embeds: list[discord.Embed] = []
    for number, description in enumerate(descriptions, start=1):
        page = "" if len(descriptions) == 1 else f" ({number}/{len(descriptions)})"
        embed = discord.Embed(
            title=f"{name} — {entry.reference_type.label}{page}",
            description=description,
            color=discord.Colour.blurple(),
        )
        footer = f"{SRD_NAME} - {entry.reference_type.label} - {SOURCE_NAME}"
        if legacy_alias:
            footer = f"{footer} | {LEGACY_RULE_HINT}"
        embed.set_footer(text=footer)
        embeds.append(embed)
    return embeds[:MAX_REFERENCE_PAGES]


def rule_embeds(rule: dict[str, Any]) -> list[discord.Embed]:
    """Compatibility wrapper for the original rule embed helper."""
    entry = ReferenceEntry(
        index=rule.get("index", "rule"),
        name=rule.get("name", DEFAULT_REFERENCE_NAME),
        url=rule.get("url", ""),
        reference_type=RULE,
    )
    return reference_embeds(entry, rule)


def search_result_embeds(
    query: str,
    results: list[SearchResult],
) -> list[discord.Embed]:
    """Group ranked search results into compact paginator pages."""
    pages: list[discord.Embed] = []
    chunks = [
        results[index : index + SEARCH_RESULTS_PER_PAGE]
        for index in range(0, len(results), SEARCH_RESULTS_PER_PAGE)
    ]
    for page_number, chunk in enumerate(chunks, start=1):
        page = "" if len(chunks) == 1 else f" ({page_number}/{len(chunks)})"
        embed = discord.Embed(
            title=f'SRD search: "{query[:100]}"{page}',
            color=discord.Colour.blurple(),
        )
        offset = (page_number - 1) * SEARCH_RESULTS_PER_PAGE
        for position, result in enumerate(chunk, start=offset + 1):
            embed.add_field(
                name=(
                    f"{position}. {result.entry.name} "
                    f"— {result.entry.reference_type.label}"
                ),
                value=result.excerpt,
                inline=False,
            )
        embed.set_footer(
            text=f"{SRD_NAME} - {len(results)} result(s) - {SOURCE_NAME}"
        )
        pages.append(embed)
    return pages


class Rules(commands.Cog):
    rules = SlashCommandGroup(
        "rules",
        RULES_GROUP_DESCRIPTION,
        guild_ids=COMMAND_GUILD_IDS,
    )

    def __init__(self, bot: commands.Bot, client: DnDAPI | None = None):
        self.bot = bot
        self.client = client or DnDAPI()
        self.catalog = ReferenceCatalog(self.client)
        self.search_index = ReferenceSearchIndex(self.client)

    async def load_references(self) -> None:
        try:
            await self.catalog.load()
            await self.search_index.load(self.catalog.entries)
            logger.info(
                "Loaded %s SRD references for autocomplete and full-text search",
                len(self.catalog.entries),
            )
        except DnDAPIError:
            logger.exception("Could not preload SRD references")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.catalog.entries or not self.search_index.documents:
            await self.load_references()

    async def reference_autocomplete(
        self,
        ctx: discord.AutocompleteContext,
    ) -> list[discord.OptionChoice]:
        return self.catalog.choices(ctx.value or "")

    async def rule_autocomplete(
        self,
        ctx: discord.AutocompleteContext,
    ) -> list[discord.OptionChoice]:
        return self.catalog.choices(ctx.value or "", RULE)

    @rules.command(name="lookup", description=LOOKUP_COMMAND_DESCRIPTION)
    async def lookup(
        self,
        ctx: discord.ApplicationContext,
        term: Annotated[
            str,
            discord.Option(
                description=REFERENCE_OPTION_DESCRIPTION,
                autocomplete=reference_autocomplete,
            ),
        ],
    ) -> None:
        await self._respond_with_reference(ctx, term)

    @rules.command(name="search", description=SEARCH_COMMAND_DESCRIPTION)
    async def search(
        self,
        ctx: discord.ApplicationContext,
        text: Annotated[
            str,
            discord.Option(description=SEARCH_OPTION_DESCRIPTION),
        ],
    ) -> None:
        await ctx.defer()
        if not self.search_index.documents:
            await ctx.respond(SEARCH_NOT_READY_MESSAGE, ephemeral=True)
            return
        try:
            results = self.search_index.search(text)
        except InvalidSearchQuery as exc:
            await ctx.respond(str(exc), ephemeral=True)
            return
        if not results:
            await ctx.respond(NO_SEARCH_RESULTS_MESSAGE, ephemeral=True)
            return

        embeds = search_result_embeds(text, results)
        if len(embeds) == 1:
            await ctx.respond(embed=embeds[0])
        else:
            paginator = Paginator(
                pages=embeds,
                show_disabled=False,
                timeout=PAGINATOR_TIMEOUT_SECONDS,
            )
            await paginator.respond(ctx.interaction, ephemeral=False)

    @discord.slash_command(name="rule", description=RULE_COMMAND_DESCRIPTION)
    async def rule(
        self,
        ctx: discord.ApplicationContext,
        name: Annotated[
            str,
            discord.Option(
                description=RULE_OPTION_DESCRIPTION,
                autocomplete=rule_autocomplete,
            ),
        ],
    ) -> None:
        await self._respond_with_reference(ctx, name, RULE, legacy_alias=True)

    async def _respond_with_reference(
        self,
        ctx: discord.ApplicationContext,
        term: str,
        reference_type: ReferenceType | None = None,
        legacy_alias: bool = False,
    ) -> None:
        await ctx.defer()
        try:
            entry, payload = await self.catalog.resolve(term, reference_type)
            embeds = reference_embeds(entry, payload, legacy_alias=legacy_alias)
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
            await ctx.respond(
                self._not_found_message(reference_type),
                ephemeral=True,
            )
        except DnDAPIError as exc:
            logger.error("SRD reference lookup failed: %s", exc, exc_info=True)
            await ctx.respond(str(exc), ephemeral=True)

    @staticmethod
    def _not_found_message(reference_type: ReferenceType | None) -> str:
        if reference_type == RULE:
            return RULE_NOT_FOUND_MESSAGE
        return REFERENCE_NOT_FOUND_MESSAGE


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Rules(bot))
