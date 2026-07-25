"""Shared Discord application-command response behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import discord

PRIVATE_OPTION_DESCRIPTION = "Show the response only to you"


@dataclass(frozen=True)
class ResponseSession:
    """Keep visibility consistent across a deferred command response."""

    ctx: discord.ApplicationContext
    private: bool = False

    async def defer(self) -> None:
        await self.ctx.defer(ephemeral=self.private)

    async def send(
        self,
        content: str | None = None,
        *,
        error: bool = False,
        **kwargs: Any,
    ) -> None:
        await self.ctx.respond(
            content,
            ephemeral=self.private or error,
            **kwargs,
        )
