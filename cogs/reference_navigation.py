"""Stateful Discord navigation for SRD search and reference pages."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import discord

from service.reference_catalog import ReferenceEntry
from service.reference_search import SearchResult


NAVIGATION_OWNER_MESSAGE = "Only the person who ran this command can use its controls."
MISSING_INDEXED_REFERENCE_MESSAGE = (
    "That indexed reference is no longer available. Run the search again."
)


@dataclass(frozen=True)
class NavigationSnapshot:
    mode: str
    search_page: int
    reference_entry: ReferenceEntry | None
    reference_pages: tuple[discord.Embed, ...]
    reference_page: int


class ReferenceNavigatorView(discord.ui.View):
    """Own one message while it moves between search and reference pages."""

    def __init__(
        self,
        *,
        owner_id: int,
        query: str,
        results: list[SearchResult],
        search_pages: list[discord.Embed],
        payload_for: Callable[[ReferenceEntry], dict[str, Any]],
        reference_pages: Callable[
            [ReferenceEntry, dict[str, Any]], list[discord.Embed]
        ],
        results_per_page: int,
        timeout: float,
    ) -> None:
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.owner_id = owner_id
        self.query = query
        self.results = tuple(results)
        self.search_pages = tuple(search_pages)
        self.payload_for = payload_for
        self.reference_pages_for = reference_pages
        self.results_per_page = results_per_page
        self.mode = "search"
        self.search_page = 0
        self.reference_entry: ReferenceEntry | None = None
        self.reference_pages: tuple[discord.Embed, ...] = ()
        self.reference_page = 0
        self.history: list[NavigationSnapshot] = []
        self._state_lock = asyncio.Lock()
        self._sync_controls()

    @discord.ui.select(
        placeholder="Open a full reference",
        options=[discord.SelectOption(label="Loading results", value="loading")],
        row=0,
    )
    async def result_select(
        self,
        select: discord.ui.Select,
        interaction: discord.Interaction,
    ) -> None:
        async with self._state_lock:
            entry = self._entry_for_value(select.values[0])
            if entry is None:
                await interaction.response.send_message(
                    MISSING_INDEXED_REFERENCE_MESSAGE,
                    ephemeral=True,
                )
                return
            try:
                payload = self.payload_for(entry)
            except KeyError:
                await interaction.response.send_message(
                    MISSING_INDEXED_REFERENCE_MESSAGE,
                    ephemeral=True,
                )
                return

            self.history.append(self._snapshot())
            self.mode = "reference"
            self.reference_entry = entry
            self.reference_pages = tuple(self.reference_pages_for(entry, payload))
            self.reference_page = 0
            await self._edit(interaction)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, row=1)
    async def previous_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        async with self._state_lock:
            if self.mode == "search":
                self.search_page = max(0, self.search_page - 1)
            else:
                self.reference_page = max(0, self.reference_page - 1)
            await self._edit(interaction)

    @discord.ui.button(
        label="1/1",
        style=discord.ButtonStyle.secondary,
        disabled=True,
        row=1,
    )
    async def page_indicator(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        return None

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, row=1)
    async def next_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        async with self._state_lock:
            if self.mode == "search":
                self.search_page = min(
                    len(self.search_pages) - 1,
                    self.search_page + 1,
                )
            else:
                self.reference_page = min(
                    len(self.reference_pages) - 1,
                    self.reference_page + 1,
                )
            await self._edit(interaction)

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.primary,
        disabled=True,
        row=1,
    )
    async def back_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        async with self._state_lock:
            if self.history:
                self._restore(self.history.pop())
            await self._edit(interaction)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.owner_id

    async def on_check_failure(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            NAVIGATION_OWNER_MESSAGE,
            ephemeral=True,
        )

    @property
    def current_embed(self) -> discord.Embed:
        if self.mode == "search":
            return self.search_pages[self.search_page]
        return self.reference_pages[self.reference_page]

    async def _edit(self, interaction: discord.Interaction) -> None:
        self._sync_controls()
        await interaction.response.edit_message(
            embed=self.current_embed,
            view=self,
        )

    def _sync_controls(self) -> None:
        page, page_count = self._page_position()
        self.page_indicator.label = f"{page + 1}/{page_count}"
        self.previous_button.disabled = page == 0
        self.next_button.disabled = page >= page_count - 1
        self.back_button.disabled = not self.history
        self.result_select.disabled = self.mode != "search"
        self.result_select.options = self._search_options()

    def _search_options(self) -> list[discord.SelectOption]:
        start = self.search_page * self.results_per_page
        page_results = self.results[start : start + self.results_per_page]
        return [
            discord.SelectOption(
                label=f"{result.entry.name} — {result.entry.reference_type.label}"[
                    :100
                ],
                value=result.entry.value,
                description=result.excerpt.replace("*", "").replace("\\", "")[:100],
            )
            for result in page_results
        ]

    def _page_position(self) -> tuple[int, int]:
        if self.mode == "search":
            return self.search_page, len(self.search_pages)
        return self.reference_page, len(self.reference_pages)

    def _entry_for_value(self, value: str) -> ReferenceEntry | None:
        return next(
            (result.entry for result in self.results if result.entry.value == value),
            None,
        )

    def _snapshot(self) -> NavigationSnapshot:
        return NavigationSnapshot(
            mode=self.mode,
            search_page=self.search_page,
            reference_entry=self.reference_entry,
            reference_pages=self.reference_pages,
            reference_page=self.reference_page,
        )

    def _restore(self, snapshot: NavigationSnapshot) -> None:
        self.mode = snapshot.mode
        self.search_page = snapshot.search_page
        self.reference_entry = snapshot.reference_entry
        self.reference_pages = snapshot.reference_pages
        self.reference_page = snapshot.reference_page
