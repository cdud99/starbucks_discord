# cogs/writeup.py

import os
import json
import discord
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from discord.app_commands import checks

WRITEUP_FILE = "writeups.json"


def load_writeups():
    if not os.path.exists(WRITEUP_FILE):
        return {}
    with open(WRITEUP_FILE, "r") as f:
        return json.load(f)


def save_writeups(data):
    with open(WRITEUP_FILE, "w") as f:
        json.dump(data, f, indent=4)


def add_writeup(user_id: int, reason: str):
    data = load_writeups()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"count": 0, "writeups": []}
    data[uid]["count"] += 1
    data[uid]["writeups"].append({
        "reason":
        reason,
        "timestamp":
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_writeups(data)


def get_writeups(user_id: int):
    data = load_writeups()
    return data.get(str(user_id), {"count": 0, "writeups": []})


class WriteupCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="writeup",
                          description="Give a user a formal write-up")
    @app_commands.describe(member="The user to write up",
                           reason="Reason for the write-up")
    @checks.has_permissions(administrator=True)
    async def writeup(self, interaction: discord.Interaction,
                      member: discord.Member, reason: str):
        add_writeup(member.id, reason)
        data = get_writeups(member.id)
        await interaction.response.send_message(
            f"✍️ `{member.display_name}` has been written up for: *{reason}*\n📄 `{member.display_name}` now has **{data['count']}** write-up(s)."
        )

    @app_commands.command(name="check_writeups",
                          description="View a user's write-up history")
    @app_commands.describe(member="The member to check")
    async def check_writeups(self, interaction: discord.Interaction,
                             member: discord.Member):
        data = get_writeups(member.id)
        embed = discord.Embed(
            title=f"📄 Write-ups for {member.display_name}",
            description=f"Total write-ups: `{data['count']}`",
            color=0xff5555)
        if not data["writeups"]:
            embed.add_field(name="No write-ups found",
                            value="Clean record... for now.",
                            inline=False)
        else:
            for i, entry in enumerate(data["writeups"], 1):
                embed.add_field(name=f"{i}. {entry['timestamp']}",
                                value=entry["reason"],
                                inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(WriteupCog(bot))
