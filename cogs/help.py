# cogs/help.py
import discord
from discord.ext import commands
from discord import app_commands


class Help(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help",
                          description="Displays all FrapBot 9000 \
                          commands")
    async def help_command(self, interaction: discord.Interaction):
        # test_user = await guild.fetch_member(527755142473449483)
        # content = ""
        # for command in interaction.client.tree.get_commands():
        #     perms = getattr(command, "default_permissions", None)
        #     if perms and perms.value != 0:
        #         names = [name for name,
        #                  v in discord.Permissions(perms.value) if v]
        #         # if 'manage_channels' in names:
        #         #     if not interaction.channel.permissions_for(
        #         #             interaction.user).manage_channels:
        #         #         continue
        #         content += f"/{command.name} – {', '.join(names)}\n"
        #     elif perms and perms.value == 0:
        #         content += f"/{command.name} – 🔒 Hidden from everyone\n"
        #     else:
        #         content += f"/{command.name} – 🌍 Visible to all\n"

        # await interaction.response.send_message(f"```{content}```",
        #                                         ephemeral=True)

        raw_commands = interaction.client.tree.get_commands()
        commands = {}
        for command in raw_commands:
            perms = getattr(command, "default_permissions", None)
            if perms and perms.value != 0:
                names = [name for name,
                         v in discord.Permissions(perms.value) if v]
                perms = ','.join(names)
            elif perms and perms.value == 0:
                perms = 0
            else:
                perms = ''
            commands[command] = perms
        embed = discord.Embed(
            title="☕ FrapBot 9000 – Command Menu 🤖", color=0x6f4e37)

        # General Commands
        general_commands = ''
        for command in commands:
            perms = commands[command]
            if perms == '':
                general_commands += f'`/{command.name}` - \
                {command.description}\n'
        embed.add_field(
            name='General Commands',
            value=general_commands,
            inline=False)

        # Mod Commands
        mod_commands = ''
        for command in commands:
            perms = commands[command]
            if perms != '' and perms != 0 and\
                'manage_channels' in perms and\
                interaction.channel.permissions_for(interaction.user).\
                    manage_channels:
                mod_commands += f'`/{command.name}` - \
                {command.description}\n'
        if mod_commands != '':
            embed.add_field(
                name='Mod Commands',
                value=mod_commands,
                inline=False)

        # Admin Commands
        admin_commands = ''
        for command in commands:
            perms = commands[command]
            if perms != '' and perms != 0 and\
                'administrator' in perms and\
                    interaction.user.guild_permissions.administrator:
                admin_commands += f'`/{command.name}` - \
                {command.description}\n'
        if admin_commands != '':
            embed.add_field(
                name='Admin Commands',
                value=admin_commands,
                inline=False)

        embed.set_footer(text="Caffeinate responsibly | v1.0")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
