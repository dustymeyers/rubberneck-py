import discord
import logging

class Rubberneck(discord.Bot):
    logger: logging.Logger

    def __init__(self, logger: logging.Logger):
        super().__init__()

        self.logger = logger
        

    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        self.logger.info("------")