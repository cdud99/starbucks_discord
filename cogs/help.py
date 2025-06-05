# cogs/help.py
import discord
from discord.ext import commands
from discord import app_commands


class Help(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help",
                          description="Displays all FrapBot 9000 commands")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="☕ FrapBot 9000 – Command Menu 🤖",
            description="Here’s what I can do to make your coffee life easier:",
            color=0x6f4e37)

        embed.add_field(name="`/drink`",
                        value="Sends a sassy drink suggestion",
                        inline=True)
        embed.add_field(name="`/check_writeups`",
                        value="Shows a users writeups",
                        inline=False)
        # embed.add_field(name="`/coords`",
        #                 value="Save/retrieve Minecraft coordinates",
        #                 inline=False)
        # embed.add_field(name="`/killcount`",
        #                 value="See who’s dying the most (probably you)",
        #                 inline=False)
        embed.set_footer(text="Caffeinate responsibly | v1.0")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
