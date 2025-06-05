from dotenv import load_dotenv
import os
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  # Required to read messages

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.command()
async def frap(ctx):
    await ctx.send("Here's your venti caramel frap with extra sass ☕️💅")

bot.run(TOKEN)
