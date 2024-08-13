from dotenv import load_dotenv
from discord.ext import commands
import os
import discord


load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

cogs_list = [
    'bestiary',
    'pagetest'
]

# bot: Bot = Rubberneck(intents=discord.Intents.all())

bot = commands.Bot(intents=discord.Intents.all())

@bot.slash_command()
async def ping(ctx):
    await ctx.respond("Pong!")
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

if __name__ == '__main__': # import cogs from cogs folder
    for extension in cogs_list:
        bot.load_extension(f'cogs.{extension}')



bot.run(TOKEN)