from discord import Bot
from logger import logger
from logging import Logger

class Rubberneck(Bot):
    logger: Logger

    def __init__(self, **args):
        super().__init__(**args)
        self.logger = logger
        

    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        self.logger.info("------")