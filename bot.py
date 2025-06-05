import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True  # Required to read messages

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.command()
async def frap(ctx):
    await ctx.send("Here's your venti caramel frap with extra sass ☕️💅")

bot.run("MTM4MDA1OTc1MzE3ODQ2NDMwNg.G7-8yq.o_5Hm0hT8P7lT80qog9GSMsruKTsGUVYqf97qo")
