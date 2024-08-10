from logging import Logger
from typing import List
from discord import Bot, Cog, slash_command
from discord.ext.commands import Context
from service import DnDAPIClient
from models import Monster

class Bestiary(Cog):

    client: DnDAPIClient
    logger: Logger
    bot: Bot
    __base_url: str = 'https://www.dnd5eapi.co/api/monsters'

    def __init__(self, bot, logger: Logger):
        self.bot = bot
        self.logger = logger
        self.client = DnDAPIClient(base_url=self.__base_url, logger=self.logger)
        self.logger.info("Bestiary cog loaded")

    @slash_command(description="View all monsters available in the D&D 5e SRD.")
    async def monsters(self, ctx: Context):
        """
            Returns a list of all monsters available in the D&D 5e SRD.

            ctx: Context
        
        """
        monsters: List[Monster] = self.client.get_monsters()

        await ctx.respond(f"Beasts: {[monster.to_dict() for monster in monsters]}")