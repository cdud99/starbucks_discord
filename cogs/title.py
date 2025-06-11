# cogs/title.py

import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import checks


class TitleCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # /title command
    @app_commands.command(
        name="title", description="Give a user a visible server title (role)")
    @app_commands.describe(member="Who to give the title to",
                           title="The title role name")
    @checks.has_permissions(administrator=True)
    async def title(self, interaction: discord.Interaction,
                    member: discord.Member, title: str):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=title)

        if not role:
            await interaction.response.send_message(
                f"❌ Title '{title}' does not exist. Use `/create_title` first.",
                ephemeral=True)
            return

        await member.add_roles(role)
        await interaction.response.send_message(
            f"🏷️ `{member.display_name}` has been given the **{title}** title!",
            ephemeral=False)

    # /create_title command
    @app_commands.command(
        name="create_title",
        description="Create a new role to use as a server title")
    @app_commands.describe(title="The name of the title/role",
                           color_hex="Optional color hex (e.g., #ffaa00)",
                           emoji="Optional emoji prefix")
    @checks.has_permissions(administrator=True)
    async def create_title(self,
                           interaction: discord.Interaction,
                           title: str,
                           color_hex: str = "#6f4e37",
                           emoji: str = ""):
        guild = interaction.guild

        # Format role name with emoji (optional)
        role_name = f"{emoji.strip()} {title}".strip() if emoji else title

        # Convert hex to discord.Color
        try:
            color = discord.Color(int(color_hex.strip("#"), 16))
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid color hex code. Use something like `#ffaa00`.",
                ephemeral=True)
            return

        # Check if role already exists
        if discord.utils.get(guild.roles, name=role_name):
            await interaction.response.send_message(
                f"⚠️ The title '{role_name}' already exists.", ephemeral=True)
            return

        # Create the role
        role = await guild.create_role(name=role_name,
                                       color=color,
                                       mentionable=False)
        await interaction.response.send_message(
            f"✅ Created title role: **{role_name}**", ephemeral=True)

    # /edit_title command
    @app_commands.command(name="edit_title",
                          description="Edit an existing title (role)")
    @app_commands.describe(
        old_title="The current role name",
        new_title="New name for the title (omit to keep same)",
        color_hex="New color hex (optional)",
        emoji="New emoji prefix (optional)")
    @checks.has_permissions(administrator=True)
    async def edit_title(self,
                         interaction: discord.Interaction,
                         old_title: str,
                         new_title: str = None,
                         color_hex: str = None,
                         emoji: str = ""):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=old_title)

        if not role:
            await interaction.response.send_message(
                f"❌ Title '{old_title}' not found.", ephemeral=True)
            return

        updated_name = role.name  # fallback
        updated_color = role.color

        if new_title:
            updated_name = f"{emoji.strip()} {new_title}".strip(
            ) if emoji else new_title

        if color_hex:
            try:
                updated_color = discord.Color(int(color_hex.strip("#"), 16))
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid color hex code.", ephemeral=True)
                return

        await role.edit(name=updated_name, color=updated_color)
        await interaction.response.send_message(
            f"✏️ Title updated to **{updated_name}**", ephemeral=True)

    # Error handling
    @title.error
    @create_title.error
    async def permission_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You must be an **Administrator** to use this command.",
                ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Error: {error}",
                                                    ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(TitleCog(bot))
