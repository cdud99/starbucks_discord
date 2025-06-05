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


@bot.command(name="help")
async def custom_help(ctx):
    help_text = """
☕ **FrapBot 9000 Commands** 🤖

`!frap` - Get a random Starbucks drink with attitude
`!mood` - Displays your daily shift mood
`!tipjar` - Fake tipping leaderboard
`!coords [name]` - Save Minecraft coordinates
`!home [name]` - Retrieve saved home location
`!killcount` - See who dies the most in-game

Need help? Just scream into your apron. Or type `!help` again.

✨ More features coming soon!
    """
    await ctx.send(help_text)

bot.run(TOKEN)
