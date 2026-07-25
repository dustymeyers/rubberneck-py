"""Slash commands for looking up D&D 5e SRD reference material."""

import asyncio
import os
import re
from typing import Annotated, Any

import discord
from discord.commands import SlashCommandGroup
from discord.ext import commands
from dotenv import load_dotenv

from rubberneck.cogs.reference_navigation import ReferenceNavigatorView
from rubberneck.logging import logger
from rubberneck.services.api_client import DnDAPI, DnDAPIError, ResourceNotFound
from rubberneck.services.reference_catalog import (
    RULE,
    ReferenceCatalog,
    ReferenceEntry,
    ReferenceType,
)
from rubberneck.services.reference_relations import ReferenceRelations
from rubberneck.services.reference_search import (
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
SEARCH_NOT_READY_MESSAGE = (
    "The local SRD search index is not ready yet. Try again shortly."
)
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
REFERENCE_LOAD_ATTEMPTS = 3
REFERENCE_RETRY_DELAY_SECONDS = 2


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
    index = 0
    while index < len(lines):
        line = lines[index]
        if (
            _is_markdown_table_row(line)
            and index + 1 < len(lines)
            and _is_markdown_table_separator(lines[index + 1])
        ):
            table_lines, index = _format_markdown_table(lines, index)
            formatted.extend(table_lines)
            continue
        heading = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
        formatted.append(f"**{heading.group(1)}**" if heading else line)
        index += 1
    return "\n".join(formatted).strip()


def _is_markdown_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def _table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_markdown_table_separator(line: str) -> bool:
    if not _is_markdown_table_row(line):
        return False
    cells = _table_cells(line)
    return bool(cells) and all(
        re.fullmatch(r":?-{3,}:?", cell) is not None for cell in cells
    )


def _format_markdown_table(
    lines: list[str],
    start: int,
) -> tuple[list[str], int]:
    """Translate a Markdown table into mobile-friendly labeled bullet rows."""
    headers = _table_cells(lines[start])
    output: list[str] = []
    index = start + 2
    while index < len(lines) and _is_markdown_table_row(lines[index]):
        cells = _table_cells(lines[index])
        primary = cells[0] if cells else "Entry"
        details = [
            (f"> **{headers[position].replace(':', '').strip()}:** {cell}")
            for position, cell in enumerate(cells[1:], start=1)
            if position < len(headers) and cell not in ("", "-")
        ]
        output.append(f"**{primary}**")
        output.extend(details)
        output.append("")
        index += 1
    if output and not output[-1]:
        output.pop()
    return output, index


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
        embed.set_footer(text=f"{SRD_NAME} - {len(results)} result(s) - {SOURCE_NAME}")
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
        self.relations = ReferenceRelations()
        self._reference_load_lock = asyncio.Lock()

    async def load_references(self) -> None:
        async with self._reference_load_lock:
            if self.catalog.entries and self.search_index.documents:
                return
            for attempt in range(1, REFERENCE_LOAD_ATTEMPTS + 1):
                try:
                    await self.catalog.load()
                    await self.search_index.load(self.catalog.entries)
                except DnDAPIError:
                    if attempt == REFERENCE_LOAD_ATTEMPTS:
                        logger.exception(
                            "Could not preload SRD references after %s attempts",
                            REFERENCE_LOAD_ATTEMPTS,
                        )
                        return
                    logger.warning(
                        "Could not preload SRD references "
                        "(attempt %s/%s); retrying in %s seconds",
                        attempt,
                        REFERENCE_LOAD_ATTEMPTS,
                        REFERENCE_RETRY_DELAY_SECONDS,
                    )
                    await asyncio.sleep(REFERENCE_RETRY_DELAY_SECONDS)
                else:
                    missing_relations = self.relations.missing_targets(
                        self.catalog.entries
                    )
                    if missing_relations:
                        logger.warning(
                            "Ignoring %s missing related-reference targets: %s",
                            len(missing_relations),
                            ", ".join(sorted(missing_relations)),
                        )
                    logger.info(
                        "Loaded %s SRD references and %s autocomplete queries "
                        "in %.1f ms (%.1f KiB)",
                        len(self.catalog.entries),
                        self.catalog.autocomplete_metrics.query_count,
                        self.catalog.autocomplete_metrics.build_milliseconds,
                        self.catalog.autocomplete_metrics.index_bytes / 1024,
                    )
                    return

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
            await self.load_references()
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
        view = ReferenceNavigatorView(
            owner_id=ctx.author.id,
            query=text,
            results=results,
            search_pages=embeds,
            payload_for=self.search_index.payload_for,
            reference_pages=reference_embeds,
            related_for=lambda entry: self.relations.related(
                entry,
                self.catalog.entries,
            ),
            results_per_page=SEARCH_RESULTS_PER_PAGE,
            timeout=PAGINATOR_TIMEOUT_SECONDS,
        )
        await ctx.respond(embed=embeds[0], view=view)

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
            view = ReferenceNavigatorView(
                owner_id=ctx.author.id,
                query="",
                results=[],
                search_pages=[],
                payload_for=self.search_index.payload_for,
                reference_pages=reference_embeds,
                related_for=lambda selected: self.relations.related(
                    selected,
                    self.catalog.entries,
                ),
                results_per_page=SEARCH_RESULTS_PER_PAGE,
                timeout=PAGINATOR_TIMEOUT_SECONDS,
                initial_reference=entry,
                initial_reference_pages=embeds,
            )
            await ctx.respond(embed=embeds[0], view=view)
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
