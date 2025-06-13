import os
import json
import datetime

from collections import defaultdict

import discord
from discord import app_commands
from discord.app_commands import checks
from discord.ext import commands, tasks
from discord.ui import View, Button, Modal, TextInput

DATA_FILE = "channel_requests.json"
LAST_REQUEST_FILE = "last_requests.json"
CHANNEL_FILE = "channel_data.json"
PENDING_REQUESTS_FILE = "pending_requests.json"


def load_last_requests():
    if os.path.exists(LAST_REQUEST_FILE):
        with open(LAST_REQUEST_FILE, "r") as f:
            return {
                int(k): datetime.datetime.fromisoformat(v)
                for k, v in json.load(f).items()
            }
    return defaultdict(lambda: datetime.datetime.min)


def save_last_requests(data):
    with open(LAST_REQUEST_FILE, "w") as f:
        json.dump({str(k): v.isoformat() for k, v in data.items()}, f)


def load_channel_data():
    if os.path.exists(CHANNEL_FILE):
        with open(CHANNEL_FILE, "r") as f:
            return json.load(f)
    return {}


def save_channel_data(data):
    with open(CHANNEL_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_request_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_request_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_pending_requests():
    if os.path.exists(PENDING_REQUESTS_FILE):
        with open(PENDING_REQUESTS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_pending_requests(data):
    with open(PENDING_REQUESTS_FILE, "w") as f:
        json.dump(data, f)


request_log_data = load_request_data()


async def build_request_embed(bot, data_key):
    data = request_log_data[data_key]
    guild = bot.get_guild(data['guild_id'])
    timestamp = datetime.datetime.strptime(
        data['timestamp'], '%Y-%m-%d %H:%M UTC')
    user = await guild.fetch_member(data["user_id"])
    request_embed = discord.Embed(
        title="📨 New Channel Request",
        description=f'**From:** {user.mention}\n**Requested At:\
            ** {timestamp.strftime(" % Y - %m - %d % H: % M UTC")}',
        color=discord.Color.orange())
    request_embed.add_field(name="Channel Name",
                            value=data['channel_name'],
                            inline=False)
    request_embed.add_field(name="Reason",
                            value=data['reason'],
                            inline=False)
    request_embed.add_field(name="Access Type",
                            value=data['access_type'],
                            inline=True)
    request_embed.add_field(name="Channel Type",
                            value=data['channel_type'],
                            inline=False)
    if 'approved' in request_log_data[data_key]:
        request_embed.add_field(name="Approved",
                                value=request_log_data[data_key]['approved'],
                                inline=False)
    if 'denial_reason' in request_log_data[data_key]:
        request_embed.add_field(name="Denial Reason",
                                value=request_log_data[data_key]
                                ['denial_reason'],
                                inline=False)

    return request_embed


class ChannelRequestModal(Modal, title="📋 Channel Request Form"):

    def __init__(self, bot, user):
        super().__init__()
        self.bot = bot
        self.user = user
        self.channel_name = TextInput(label="Channel Name",
                                      placeholder="ex: minecraft",
                                      max_length=32)
        self.reason = TextInput(label="What’s this channel for?",
                                style=discord.TextStyle.paragraph)
        self.access = TextInput(label="Access Type (public or private)",
                                placeholder="public or private")
        self.channel_type = TextInput(label="Channel Type (text, voice, both)",
                                      placeholder="text, voice, or both")
        self.add_item(self.channel_name)
        self.add_item(self.reason)
        self.add_item(self.access)
        self.add_item(self.channel_type)

    async def on_submit(self, interaction: discord.Interaction):
        channel_name = self.channel_name.value.lower()
        channel_name = channel_name.replace(' ', '')
        access_type = self.access.value.lower()
        channel_type = self.channel_type.value.lower()

        if access_type not in ["public", "private"]:
            await interaction.response.send_message(
                "❌ Invalid access type. Please use 'public' or 'private'.",
                ephemeral=True)
            return
            return

        if channel_type not in ["text", "voice", "both"]:
            await interaction.response.send_message(
                "❌ Invalid channel type. Please use 'text', 'voice', or \
                    'both'.",
                ephemeral=True)
            return

        log_channel = discord.utils.get(interaction.guild.text_channels,
                                        name="owner")
        now = datetime.datetime.utcnow()

        data_key = str(now.timestamp())
        request_log_data[data_key] = {
            'guild_id': interaction.guild.id,
            "user": self.user.name,
            "user_id": self.user.id,
            "channel_name": channel_name,
            "reason": self.reason.value,
            "access_type": access_type,
            "channel_type": channel_type,
            "timestamp": now.strftime('%Y-%m-%d %H:%M UTC')
        }
        save_request_data(request_log_data)

        request_embed = await build_request_embed(self.bot, data_key)
        sent_msg = await log_channel.send(embed=request_embed,
                                          view=RequestApprovalView(
                                              self.bot, data_key))

        pending = load_pending_requests()
        pending[str(log_channel.id)] = {
            'message_id': sent_msg.id,
            'data_key': data_key
        }
        save_pending_requests(pending)

        await interaction.response.send_message(
            "✅ Your request has been sent for approval! Stay tuned...",
            ephemeral=True)  # Save request time persistently

        self.bot.get_cog("ChannelManager").user_last_request[
            self.user.id] = now
        save_last_requests(
            self.bot.get_cog("ChannelManager").user_last_request)


class RequestApprovalView(View):

    def __init__(self, bot, data_key):
        super().__init__(timeout=None)
        self.bot = bot
        self.data_key = data_key
        self.data = request_log_data[self.data_key]

    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success,
                       custom_id="approve_button")
    async def approve(self, interaction: discord.Interaction,
                      button: discord.ui.Button):
        guild = interaction.guild
        self.requester = await guild.fetch_member(self.data["user_id"])
        overwrites = {
            guild.default_role:
            discord.PermissionOverwrite(read_messages=False),
        }

        role = await guild.create_role(
            name=f"{self.data['channel_name']}-access")
        overwrites[role] = discord.PermissionOverwrite(read_messages=True,
                                                       send_messages=True)

        new_text_channel = None
        new_voice_channel = None

        if self.data['channel_type'] in ['text', 'both']:
            new_text_channel = await guild.create_text_channel(
                name=self.data['channel_name'],
                overwrites=overwrites,
                category=discord.utils.get(guild.categories,
                                           name="🧃 Barista Banter"))
            await new_text_channel.set_permissions(self.requester,
                                                   manage_messages=True,
                                                   manage_channels=True)

        if self.data['channel_type'] in ['voice', 'both']:
            new_voice_channel = await guild.create_voice_channel(
                name=self.data['channel_name'],
                overwrites=overwrites,
                category=discord.utils.get(guild.categories,
                                           name="📞 Barista Hotline"))
            await new_voice_channel.set_permissions(self.requester,
                                                    manage_channels=True,
                                                    mute_members=True,
                                                    move_members=True)

        await self.requester.add_roles(role, self.data['channel_name'])

        general_channel = discord.utils.get(guild.text_channels, name="owner")
        await general_channel.send(
            f"☕ A new channel **#{self.data['channel_name']}** has been \
                brewed! Click below to join.",
            view=JoinChannelView(role))
        await interaction.response.send_message(
            "☕ Channel approved and created!", ephemeral=True)
        await self.requester.send(
            f"✅ Your channel **#{self.data['channel_name']}** was approved \
                and created! You are a moderator for this channel and can \
                view your commands using `/help` in your channel."
        )

        request_log_data[self.data_key]
        save_request_data(request_log_data)

        channel_data = load_channel_data()
        channel_data[self.data['channel_name']] = {
            # 'title_name': self.data['title_name'],
            'title_name': f'{self.data["channel_name"]}-access',
            'text_channel': self.data['channel_type'] in ['text', 'both'],
            'voice_channel': self.data['channel_type'] in ['voice', 'both']
        }
        save_channel_data(channel_data)

        request_log_data[self.data_key]['approved'] = 'Yes'
        save_request_data(request_log_data)

        request_embed = await build_request_embed(self.bot, self.data_key)
        await interaction.message.edit(embed=request_embed, view=None)
        self._cleanup_pending(interaction.message.channel.id)

    @discord.ui.button(label="❌ Deny", style=discord.ButtonStyle.danger,
                       custom_id="deny_button")
    async def deny(self, interaction: discord.Interaction,
                   button: discord.ui.Button):
        self.data = request_log_data[self.data_key]
        self.requester = await interaction.guild.fetch_member(
            self.data["user_id"])
        await interaction.response.send_modal(
            DenyReasonModal(self.bot, self.requester, self.data_key,
                            interaction))
        self._cleanup_pending(interaction.message.channel.id)

    def _cleanup_pending(self, channel_id):
        pending = load_pending_requests()
        pending.pop(str(channel_id), None)
        save_pending_requests(pending)


class DenyReasonModal(Modal, title="Why Deny This?"):

    def __init__(self, bot, requester, data_key, interaction):
        super().__init__()
        self.bot = bot
        self.requester = requester
        self.reason = TextInput(label="Reason for denial",
                                style=discord.TextStyle.paragraph)
        self.add_item(self.reason)
        self.parent_interaction = interaction
        self.data_key = data_key
        self.data = request_log_data[self.data_key]

    async def on_submit(self, interaction: discord.Interaction):
        await self.requester.send(
            f"❌ Your channel request was denied. Reason: {self.reason.value}")
        request_log_data[self.data_key]['approved'] = 'No'
        request_log_data[self.data_key]['denial_reason'] = self.reason.value
        save_request_data(request_log_data)

        request_embed = await build_request_embed(self.bot, self.data_key)
        await interaction.message.edit(embed=request_embed, view=None)

        await interaction.response.send_message(
            "Request denied and user notified.", ephemeral=True)


class JoinChannelView(View):

    def __init__(self, role):
        super().__init__(timeout=None)
        self.role = role
        self.channel = channel

    @discord.ui.button(label="Join Channel", style=discord.ButtonStyle.primary)
    async def join(self, interaction: discord.Interaction,
                   button: discord.ui.Button):
        await interaction.user.add_roles(self.role)
        await interaction.response.send_message(
            f"✅ You now have the title **{self.role.name}** and access to \
                **#{self.channel}!",
            ephemeral=True)


class ChannelManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.user_last_request = load_last_requests()
        self.bot.loop.create_task(self.restore_pending_views())

    async def restore_pending_views(self):
        await self.bot.wait_until_ready()
        pending = load_pending_requests()
        for channel_id_str, data in pending.items():
            message_id = data['message_id']
            data_key = data['data_key']
            channel = self.bot.get_channel(int(channel_id_str))
            if channel:
                try:
                    await channel.fetch_message(message_id)
                    self.bot.add_view(
                        RequestApprovalView(self.bot, data_key))
                except discord.NotFound:
                    continue

    @app_commands.command(name="request_channel",
                          description="Request a new channel")
    async def request_channel(self, interaction: discord.Interaction):
        now = datetime.datetime.utcnow()
        last = self.user_last_request.get(interaction.user.id,
                                          datetime.datetime.min)
        if (now - last).total_seconds() < 86400:
            await interaction.response.send_message(
                "⏳ You can only request one channel per day. Try again later!",
                ephemeral=True)
            return
        await interaction.response.send_modal(
            ChannelRequestModal(self.bot, interaction.user))

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(
        name="reset_channel_cooldown",
        description="Reset a user's channel request cooldown")
    @checks.has_permissions(administrator=True)
    async def reset_channel_cooldown(self,
                                     interaction: discord.Interaction,
                                     user: discord.Member = None):
        target = user or interaction.user
        if target.id in self.user_last_request:
            del self.user_last_request[target.id]
            save_last_requests(self.user_last_request)
            await interaction.response.send_message(
                f"✅ Cooldown for {target.mention} has been reset.",
                ephemeral=True)
        else:
            await interaction.response.send_message(
                f"ℹ️ No cooldown found for {target.mention}.", ephemeral=True)

    @app_commands.default_permissions(manage_channels=True)
    @app_commands.command(name="invite_to_channel",
                          description="Invite a user to the channel")
    async def invite_to_channel(self, interaction: discord.Interaction,
                                member: discord.Member):
        channel_data = load_channel_data()
        title_name = channel_data.get(interaction.channel.name,
                                      {}).get('title_name', '')
        if interaction.channel.permissions_for(
                interaction.user).manage_channels:
            await member.add_roles(title_name)
            await interaction.response.send_message(
                f"✅ {member.mention} has been invited to your channel!",
                ephemeral=True)
            return
        await interaction.response.send_message(
            "❌ You must be a mod in this channel to invite users.",
            ephemeral=True)

    @app_commands.default_permissions(manage_channels=True)
    @app_commands.command(name="remove_from_channel",
                          description="Remove a user from the channel")
    async def remove_from_channel(self, interaction: discord.Interaction,
                                  member: discord.Member):
        channel_data = load_channel_data()
        title_name = channel_data.get(interaction.channel.name,
                                      {}).get('title_name', '')
        if interaction.channel.permissions_for(
                interaction.user).manage_channels:
            await member.remove_roles(title_name)
            await interaction.response.send_message(
                f"🚫 {member.mention} has been removed from the channel.",
                ephemeral=True)
            return
        await interaction.response.send_message(
            "❌ You must be a mod in this channel to remove users.",
            ephemeral=True)

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name='remove_channel',
                          description='Remove a channel')
    async def remove_channel(
            self, interaction: discord.Interaction, channel: str):
        channel_data = load_channel_data()
        if channel in channel_data:
            entry = channel_data[channel]
            deleted = []

            # Try to delete text channel
            if entry.get("text_channel"):
                text = discord.utils.get(
                    interaction.guild.text_channels, name=channel)
                if text:
                    await text.delete(reason=f"Deleted by {interaction.user}")
                    deleted.append(f"📄 #{channel}")

            # Try to delete voice channel
            if entry.get("voice_channel"):
                voice = discord.utils.get(
                    interaction.guild.voice_channels, name=channel)
                if voice:
                    await voice.delete(reason=f"Deleted by {interaction.user}")
                    deleted.append(f"🔊 {channel} (voice)")

            # Delete associated role
            role = discord.utils.get(
                interaction.guild.roles, name=entry['title_name'])
            if role:
                await role.delete(reason=f"Deleted by {interaction.user}")
                deleted.append(f"👥 {role.name}")

            # Remove from JSON
            del channel_data[channel]
            save_channel_data(channel_data)

            if deleted:
                await interaction.response.send_message(
                    f"✅ Deleted:\n" + "\n".join(deleted), ephemeral=True)
            else:
                await interaction.response.send_message(
                    "⚠️ No matching channels or roles found.", ephemeral=True)
        return


async def setup(bot):
    await bot.add_cog(ChannelManager(bot))
