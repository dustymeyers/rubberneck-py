import logging
from src import Rubberneck, setup_logger
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

logger = setup_logger(logging.DEBUG)

bot = Rubberneck(logger)

@bot.slash_command()
async def ping(ctx):
    await ctx.respond("Pong!")

bot.run(TOKEN)