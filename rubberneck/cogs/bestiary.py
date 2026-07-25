"""Slash commands for browsing D&D 5e SRD monsters."""

import asyncio
import os
from typing import Annotated, Any

import discord
from discord.ext import commands
from discord.ext.pages import Paginator
from dotenv import load_dotenv

from rubberneck.cogs.responses import PRIVATE_OPTION_DESCRIPTION, ResponseSession
from rubberneck.logging import logger
from rubberneck.services.api_client import (
    DnDAPI,
    DnDAPIError,
    ResourceNotFound,
)
from rubberneck.services.reference_catalog import (
    ReferenceCatalog,
    ReferenceEntry,
    ReferenceType,
)

MONSTER = ReferenceType(key="monster", label="Monster", endpoint="monsters")
MONSTERS_PER_PAGE = 20
MONSTER_LOAD_ATTEMPTS = 3
MONSTER_RETRY_DELAY_SECONDS = 2
MONSTER_NOT_FOUND_MESSAGE = (
    "I couldn't find that SRD monster. Start typing the name and choose a suggestion."
)
MONSTERS_NOT_READY_MESSAGE = (
    "The SRD monster catalog is not ready yet. Try again shortly."
)
MONSTER_OPTION_DESCRIPTION = "Monster name, such as 'Adult Black Dragon'"
SRD_NAME = "D&D 5e SRD (2014)"
SOURCE_NAME = "dnd5eapi.co"

load_dotenv()
CONFIGURED_GUILD_ID = os.getenv("GUILD_ID")
COMMAND_GUILD_IDS = [int(CONFIGURED_GUILD_ID)] if CONFIGURED_GUILD_ID else None


def chunk_entries(
    entries: list[ReferenceEntry],
    size: int = MONSTERS_PER_PAGE,
) -> list[list[ReferenceEntry]]:
    """Split entries into non-empty, bounded paginator pages."""
    if size < 1:
        raise ValueError("Page size must be at least one.")
    return [entries[index : index + size] for index in range(0, len(entries), size)]


def monster_list_embeds(entries: list[ReferenceEntry]) -> list[discord.Embed]:
    """Build compact, alphabetized monster-list pages."""
    chunks = chunk_entries(sorted(entries, key=lambda entry: entry.name.casefold()))
    embeds: list[discord.Embed] = []
    for page_number, chunk in enumerate(chunks, start=1):
        embed = discord.Embed(
            title=f"SRD Monsters ({page_number}/{len(chunks)})",
            description="\n".join(f"• {entry.name}" for entry in chunk),
            color=discord.Colour.blurple(),
        )
        embed.set_footer(text=f"{SRD_NAME} - {len(entries)} monsters - {SOURCE_NAME}")
        embeds.append(embed)
    return embeds


def monster_embed(payload: dict[str, Any]) -> discord.Embed:
    """Build a readable summary from a monster API payload."""
    name = payload.get("name", "SRD Monster")
    monster_type = " ".join(
        part
        for part in (
            payload.get("size"),
            payload.get("type"),
            payload.get("subtype"),
        )
        if part
    )
    alignment = payload.get("alignment")
    description = ", ".join(part for part in (monster_type, alignment) if part)
    embed = discord.Embed(
        title=name,
        description=description or None,
        color=discord.Colour.blurple(),
    )

    armor_class = payload.get("armor_class", [])
    armor_values = [
        str(item.get("value")) if isinstance(item, dict) else str(item)
        for item in armor_class
    ]
    speed = payload.get("speed", {})
    speed_text = ", ".join(f"{kind.title()} {value}" for kind, value in speed.items())
    embed.add_field(name="Armor Class", value=", ".join(armor_values) or "—")
    embed.add_field(name="Hit Points", value=str(payload.get("hit_points", "—")))
    embed.add_field(name="Speed", value=speed_text or "—")

    ability_names = (
        ("STR", "strength"),
        ("DEX", "dexterity"),
        ("CON", "constitution"),
        ("INT", "intelligence"),
        ("WIS", "wisdom"),
        ("CHA", "charisma"),
    )
    abilities = "  ".join(
        f"**{label}** {payload.get(key, '—')}" for label, key in ability_names
    )
    embed.add_field(name="Ability Scores", value=abilities, inline=False)
    embed.add_field(
        name="Challenge",
        value=(
            f"CR {payload.get('challenge_rating', '—')} ({payload.get('xp', '—')} XP)"
        ),
    )
    embed.add_field(
        name="Languages",
        value=payload.get("languages") or "—",
    )

    for heading, key in (
        ("Special Abilities", "special_abilities"),
        ("Actions", "actions"),
        ("Legendary Actions", "legendary_actions"),
    ):
        items = payload.get(key) or []
        if items:
            text = "\n\n".join(
                f"**{item.get('name', heading)}.** {item.get('desc', '')}".strip()
                for item in items
            )
            embed.add_field(name=heading, value=text[:1024], inline=False)

    embed.set_footer(text=f"{SRD_NAME} - Monster - {SOURCE_NAME}")
    return embed


class Bestiary(commands.Cog):
    def __init__(self, bot: commands.Bot, client: DnDAPI | None = None):
        self.bot = bot
        self.client = client or DnDAPI()
        self.catalog = ReferenceCatalog(self.client, (MONSTER,))
        self._load_lock = asyncio.Lock()

    async def load_monsters(self) -> None:
        async with self._load_lock:
            if self.catalog.entries:
                return
            for attempt in range(1, MONSTER_LOAD_ATTEMPTS + 1):
                try:
                    await self.catalog.load()
                except DnDAPIError:
                    if attempt == MONSTER_LOAD_ATTEMPTS:
                        logger.exception(
                            "Could not preload SRD monsters after %s attempts",
                            MONSTER_LOAD_ATTEMPTS,
                        )
                        return
                    logger.warning(
                        "Could not preload SRD monsters (attempt %s/%s); "
                        "retrying in %s seconds",
                        attempt,
                        MONSTER_LOAD_ATTEMPTS,
                        MONSTER_RETRY_DELAY_SECONDS,
                    )
                    await asyncio.sleep(MONSTER_RETRY_DELAY_SECONDS)
                else:
                    logger.info(
                        "Loaded %s SRD monsters and %s autocomplete queries "
                        "in %.1f ms (%.1f KiB)",
                        len(self.catalog.entries),
                        self.catalog.autocomplete_metrics.query_count,
                        self.catalog.autocomplete_metrics.build_milliseconds,
                        self.catalog.autocomplete_metrics.index_bytes / 1024,
                    )
                    return

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.catalog.entries:
            await self.load_monsters()

    async def monster_autocomplete(
        self,
        ctx: discord.AutocompleteContext,
    ) -> list[discord.OptionChoice]:
        return self.catalog.choices(ctx.value or "", MONSTER)

    @discord.slash_command(
        name="monsters",
        description="Browse monsters available in the D&D 5e SRD.",
        guild_ids=COMMAND_GUILD_IDS,
    )
    async def monsters(
        self,
        ctx: discord.ApplicationContext,
        private: Annotated[
            bool,
            discord.Option(description=PRIVATE_OPTION_DESCRIPTION),
        ] = False,
    ) -> None:
        response = ResponseSession(ctx, private)
        await response.defer()
        if not self.catalog.entries:
            await self.load_monsters()
        if not self.catalog.entries:
            await response.send(MONSTERS_NOT_READY_MESSAGE, error=True)
            return

        pages = monster_list_embeds(self.catalog.entries)
        paginator = Paginator(pages=pages)
        await paginator.respond(ctx.interaction, ephemeral=private)

    @discord.slash_command(
        name="monster",
        description="Look up a specific D&D 5e SRD monster.",
        guild_ids=COMMAND_GUILD_IDS,
    )
    async def monster(
        self,
        ctx: discord.ApplicationContext,
        name: Annotated[
            str,
            discord.Option(
                description=MONSTER_OPTION_DESCRIPTION,
                autocomplete=monster_autocomplete,
            ),
        ],
        private: Annotated[
            bool,
            discord.Option(description=PRIVATE_OPTION_DESCRIPTION),
        ] = False,
    ) -> None:
        response = ResponseSession(ctx, private)
        await response.defer()
        try:
            _, payload = await self.catalog.resolve(name, MONSTER)
        except ResourceNotFound:
            await response.send(MONSTER_NOT_FOUND_MESSAGE, error=True)
            return
        except DnDAPIError as exc:
            logger.error("SRD monster lookup failed: %s", exc, exc_info=True)
            await response.send(str(exc), error=True)
            return
        await response.send(embed=monster_embed(payload))


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Bestiary(bot))
