from logging import Logger
import os
from typing import List
from discord import slash_command, Embed, Bot, ApplicationContext, Colour
from discord.ext import commands
from service import DnDAPIClient
from models import Monster
from logger import logger
from dotenv import load_dotenv
from discord.ext.pages import Page,PageGroup,Paginator, PaginatorButton


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
        

    @slash_command(name='monsters', description="Returns a list of all monsters available in the D&D 5e SRD.")
    async def monsters(self, ctx: ApplicationContext):
        """
            Returns a list of all monsters available in the D&D 5e SRD.
        
        """
        try:
            monsters: List[Monster] = self.client.get_monsters()

            pages = []

            monster_chunks = self.chunk_monsters(monsters)

            total_pages = len(monster_chunks)

            for page_number, chunk in enumerate(monster_chunks, start=1):
                self.logger.debug(f"Creating page {page_number} of {total_pages}")
                pages.append(self.make_monster_embed(chunk))
            
            paginator = Paginator(pages=pages)

            await paginator.respond(ctx.interaction, ephemeral=False)

        except Exception as e:
            self.logger.error(f"Error: {e}", exc_info=True)
            await ctx.respond(f"Error: {e}")

    @slash_command(name='monster', description="Returns a specific monster.")
    async def monster(self, ctx: ApplicationContext, name: str):
        """
            Returns a specific monster.
        """
        try:
            monster: Monster = self.client.get_monster(name)
            embed = self.make_monster_embed([monster])
            await ctx.respond(embed=embed)
        except Exception as e:
            self.logger.error(f"Error: {e}", exc_info=True)
            await ctx.respond(f"Error: {e}")

    def chunk_monsters(self, monsters: List[Monster], max_chunk_size: int = 25) -> List[List[Monster]]:
        """
        Splits a list of monsters into chunks of up to `max_chunk_size` elements.
        Each chunk will contain at least one monster.

        Args:
            monsters (List[Monster]): The list of monsters to be chunked.
            max_chunk_size (int, optional): The maximum size of each chunk. Defaults to 25.

        Returns:
            List[List[Monster]]: A list of chunks, where each chunk is a list of up to `max_chunk_size` monsters.
        """
        chunks = []
        for i in range(0, len(monsters), max_chunk_size):
            chunk = monsters[i:i + max_chunk_size]
            if chunk:
                chunks.append(chunk)
        return chunks

    def make_monster_embed(self, monsters: List[Monster]) -> Embed:
        """
            Returns an embed with a list of monsters.
            Maximum length of 25 monsters.
        """
        if len(monsters) > 25:
            self.logger.warning("Maximum number of monsters exceeded. Returning first 25 monsters.")
            monsters = monsters[:25]

        embed = Embed(
                title="Monsters",
                description="A list of all monsters available in the D&D 5e SRD.",
                color = Colour.blurple(),
            )
        
        try:
            for monster in monsters:
                if monster is None:
                    continue
                else:
                    self.logger.debug(f"Adding monster {monster.name} to embed")
                    embed.add_field(name=monster.name, value=monster.url, inline=True)
        except Exception as e:
            raise e
        
        return embed

def setup(bot):
    bot.add_cog(Bestiary(bot))
    