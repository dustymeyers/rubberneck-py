from logging import Logger
import os
from typing import List
from discord import slash_command, Embed, Bot, ApplicationContext, Colour
from discord.ext import commands
from service import DnDAPIClient
from models import Monster
from logger import logger
from dotenv import load_dotenv

load_dotenv()

GUILD_ID = os.getenv('GUILD_ID')

class Bestiary(commands.Cog):

    client: DnDAPIClient
    logger: Logger
    bot: Bot
    __base_url: str = 'https://www.dnd5eapi.co/api/monsters'

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logger
        self.client = DnDAPIClient(base_url=self.__base_url)
        self.logger.info("Bestiary cog loaded")
        

    @slash_command(guild_ids=[GUILD_ID],name='monsters', description="Returns a list of all monsters available in the D&D 5e SRD.")
    async def monsters(self, ctx: ApplicationContext):
        """
            Returns a list of all monsters available in the D&D 5e SRD.
        
        """
        try:
            monsters: List[Monster] = self.client.get_monsters()

            embed = Embed(
                title="Monsters",
                description="A list of all monsters available in the D&D 5e SRD.",
                color = Colour.blurple(),
            )

            random_monsters: List[Monster] = monsters[:25]
            for monster in random_monsters:
                embed.add_field(name=monster.name, value=monster.url, inline=True)

            # TODO: modify this to use embed for displaying te list monsters
            await ctx.respond(f"Here's some monsters", embed=embed)

        except Exception as e:
            self.logger.error(f"Error: {e}")
            await ctx.respond(f"Error: {e}")
        # await ctx.respond(f"Beasts: {monsters[1].to_dict()['name']}")

def setup(bot):
    bot.add_cog(Bestiary(bot))
    