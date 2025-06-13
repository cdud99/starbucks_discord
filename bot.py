import os
import random
import discord
from dotenv import load_dotenv
from discord.ext import commands, tasks
from keep_alive import keep_alive

import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  # Required to read messages

# keep_alive()

bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

# List of (ActivityType, message) tuples

statuses = [
    # Playing
    (discord.ActivityType.playing, "with the espresso machine settings again"),
    (discord.ActivityType.playing, "Minecraft while ignoring customers"),
    (discord.ActivityType.playing, "barista simulator"),
    (discord.ActivityType.playing, "hide and seek with customers"),
    (discord.ActivityType.playing, "milk roulette"),
    (discord.ActivityType.playing, "coffee pong in the backroom"),

    # Watching
    (discord.ActivityType.watching, "the beans run out"),
    (discord.ActivityType.watching, "mobile orders wait"),
    (discord.ActivityType.watching, "the shift lose it"),
    (discord.ActivityType.watching, "my coworkers mentally clock out"),
    (discord.ActivityType.watching, "a barista cry"),
    (discord.ActivityType.watching, "you clean the bathroom again"),
    (discord.ActivityType.watching, "TikToks during a rush"),

    # Listening
    (discord.ActivityType.listening, "to partners trauma dump"),
    (discord.ActivityType.listening, "to “hi welcome in”"),
    (discord.ActivityType.listening,
     "to customer complaints about too much ice"),

    # Competing
    (discord.ActivityType.competing, "in Starbucks Hunger Games"),
    (discord.ActivityType.competing,
     "for Most Emotionally Stable Barista (lost)"),
    (discord.ActivityType.competing,
     "in today’s passive-aggressive shift showdown"),
    (discord.ActivityType.competing, "for “who gets cut first” speedrun"),
    (discord.ActivityType.competing, "in the 60-second milk restock race"),
    (discord.ActivityType.competing, "for title of Bean King"),
    (discord.ActivityType.competing, "against the laws of coffee"),

    # Streaming
    (discord.ActivityType.streaming, "Latte Speedruns LIVE"),
    (discord.ActivityType.streaming, "Unhinged Barista Stories: Season 5"),
    (discord.ActivityType.streaming, "Blender ASMR: Chaos Edition"),
    (discord.ActivityType.streaming, "“How Not to Make a Frap” masterclass"),
    (discord.ActivityType.streaming, "The Espresso Olympics"),
    (discord.ActivityType.streaming, "1000 Orders, No Tips Challenge"),
    (discord.ActivityType.streaming, "Shift Simulator 3000"),
    (discord.ActivityType.streaming, "Brewing Trouble: Live"),
    (discord.ActivityType.streaming, "The Great Customer Service Meltdown"),
]


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    try:
        synced = await bot.tree.sync()
        print(f'Logged in as {bot.user}')
        print(f"Synced {len(synced)} command(s).")
        rotate_status.start()
    except Exception as e:
        print(f"Sync failed: {e}")


@bot.event
async def setup_hook():
    # Load all cogs in the cogs folder
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')


@tasks.loop(seconds=3600)
async def rotate_status():
    activity_type, message = random.choice(statuses)
    await bot.change_presence(activity=discord.Activity(type=activity_type,
                                                        name=message),
                              status=discord.Status.online)

bot.run(TOKEN)
