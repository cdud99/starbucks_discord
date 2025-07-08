import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime
import os
import json
import requests
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

load_dotenv()
MINECRAFT_FILE = 'minecraft_data.json'
REALM_ID = os.getenv('REALM_ID')
TOKEN_FILE = "realm_token.json"
ALERT_CHANNEL_NAME = "minecraft"
CHECK_INTERVAL = 60  # seconds


def load_minecraft_data():
    if os.path.exists(MINECRAFT_FILE):
        with open(MINECRAFT_FILE, "r") as f:
            return json.load(f)
    return {}


def save_minecraft_data(data):
    with open(MINECRAFT_FILE, "w") as f:
        json.dump(data, f, indent=4)


class RealmTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_realm.start()

    def fetch_new_token(self):
        minecraft_data = load_minecraft_data()
        url = 'https://login.live.com/oauth20_token.srf'
        data = {
            "client_id": "d04f99bb-edd4-4123-9829-2cb348b54a1c",
            "grant_type": "refresh_token",
            "refresh_token": minecraft_data['refresh_token'],
            "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
            "scope": "XboxLive.signin offline_access"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(url, data=data, headers=headers)

        # print("Status Code", response.status_code)
        if response.status_code != 200:
            print('Access Tokens:', response)
        response_json = response.json()
        minecraft_data['access_token'] = response_json['access_token']
        minecraft_data['refresh_token'] = response_json['refresh_token']
        save_minecraft_data(minecraft_data)

        url = 'https://user.auth.xboxlive.com/user/authenticate'
        data = {
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": f"d={minecraft_data['access_token']}"
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT"
        }
        response = requests.post(url, json=data)
        # print("Status Code", response.status_code)
        if response.status_code != 200:
            print('User Token:', response)
        response_json = response.json()
        minecraft_data['user_token'] = response_json['Token']
        save_minecraft_data(minecraft_data)
        return minecraft_data

    def reauthenticate(self, relying_party):
        minecraft_data = load_minecraft_data()
        url = 'https://xsts.auth.xboxlive.com/xsts/authorize'
        running = True
        while running:
            running = False
            data = {
                "Properties": {
                    "SandboxId": "RETAIL",
                    "UserTokens": [minecraft_data['user_token']]
                },
                "RelyingParty": relying_party,
                "TokenType": "JWT"
            }
            response = requests.post(url, json=data)

            # print("Status Code", response.status_code)
            if response.status_code == 401:
                print('Fetching new tokens')
                running = True
                minecraft_data = self.fetch_new_token()
                continue
            elif response.status_code == 200:
                response_json = response.json()
                location = ''
                if 'realm' in relying_party:
                    location = 'realm'
                elif 'xbox' in relying_party:
                    location = 'xbox'
                minecraft_data[f'{location}_token'] = response_json['Token']
                minecraft_data[f'{location}_uhs'] = response_json['DisplayClaims']['xui'][0]['uhs']
                save_minecraft_data(minecraft_data)
                return minecraft_data
            else:
                print(response)


    def get_player_name(self, uuid):
        print(f'Getting player name for:', uuid)
        minecraft_data = load_minecraft_data()
        if 'xbox_uhs' not in minecraft_data or minecraft_data['xbox_uhs'] == '':
            minecraft_data = self.reauthenticate('http://xboxlive.com')
        url = f"https://profile.xboxlive.com/users/xuid({uuid})/profile/settings?settings=ModernGamertag"
        running = True
        while running:
            running = False
            headers = {
                'Authorization': f'XBL3.0 x={minecraft_data["xbox_uhs"]};{minecraft_data["xbox_token"]}',
                'x-xbl-contract-version': '2',
            }
            response = requests.get(url, headers=headers)

            # print("Status Code", response.status_code)
            if response.status_code == 401:
                print('Reauthenticating at get_player_name')
                running = True
                minecraft_data = self.reauthenticate('http://xboxlive.com')
                continue
            elif response.status_code == 200:
                response_json = response.json()
                print('Got player name:', response_json['profileUsers'][0]['settings'][0]['value'])
                return response_json['profileUsers'][0]['settings'][0]['value']
            else:
                print(response)

    def time_difference(self, start_time):
        end_time = datetime.now()

        # Calculate the time difference as a timedelta object
        time_diff = end_time - start_time

        # Extract total seconds from timedelta
        total_seconds = int(time_diff.total_seconds())

        # Calculate hours and minutes
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        return hours, minutes

    async def process_player_data(self):
        # print('Processing player data')
        minecraft_data = load_minecraft_data()
        current_player_data = minecraft_data['current_player_data']
        cached_player_data = minecraft_data['players']
        for player in current_player_data:
            player_exists = False
            cached_player_index = None
            for index, cached_player in enumerate(cached_player_data):
                if cached_player['uuid'] == player['uuid']:
                    cached_player_index = index
                    player_exists = True
                    break
            if not player_exists:
                if player['name'] == None:
                    name = self.get_player_name(player['uuid'])
                    player['name'] = name
                print(f'{player["name"]} joined the realm')
                # embed = discord.Embed(
                #     title="🌍 Realm Entry",
                #     description=f'**{player["name"]}** has entered the realm. Welcome!',
                #     color=discord.Color.blue(),
                #     timestamp=datetime.now()
                # )
                # embed.set_thumbnail(url=f'https://minotar.net/avatar/{player["uuid"]}')
                # embed.set_footer(text="Minecraft Realm Tracker")
                # await self.send_alert(embed)
                if player['online']:
                    now = datetime.now()
                    player['sign_on'] = now.timestamp()
                cached_player_data.append(player)
            else:
                cached_player = cached_player_data[cached_player_index]
                if cached_player['online'] and not player['online']:
                    cached_player_data[cached_player_index]['online'] = False
                    sign_on = cached_player['sign_on']
                    sign_on = datetime.fromtimestamp(sign_on)
                    hours, minutes = self.time_difference(sign_on)
                    message = f'{cached_player["name"]} just clocked out with '
                    if hours > 0:
                        message += '`{hours}` hour{"s" if hours != 1 else ""} and '
                    message += '`{minutes}` minute{"s" if minutes != 1 else ""} of productivity.'
                    print(f'{cached_player["name"]} signed off')
                    embed = discord.Embed(
                        title="📤 Player Logged Out",
                        description=f'**{cached_player["name"]}** signed off after `{hours}` hour{"s" if hours != 1 else ""} and `{minutes}` minute{"s" if minutes != 1 else ""} of productivity.',
                        color=discord.Color.red(),
                        timestamp=datetime.now()
                    )
                    embed.set_thumbnail(url=f'https://minotar.net/avatar/{cached_player["uuid"]}')
                    embed.set_footer(text="Minecraft Realm Tracker")
                    await self.send_alert(embed)
                elif not cached_player['online'] and player['online']:
                    cached_player_data[cached_player_index]['online'] = True
                    now = datetime.now()
                    cached_player_data[cached_player_index]['sign_on'] = now.timestamp()
                    print(f'{cached_player["name"]} signed in')
                    embed = discord.Embed(
                        title="☕ Player Logged In",
                        description=f'**{cached_player["name"]}** just clocked in to the realm.',
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    embed.set_thumbnail(url=f'https://minotar.net/avatar/{cached_player["uuid"]}')
                    embed.set_footer(text="Minecraft Realm Tracker")
                    await self.send_alert(embed)
        minecraft_data = load_minecraft_data()
        minecraft_data['players'] = cached_player_data
        del minecraft_data['current_player_data']
        save_minecraft_data(minecraft_data)
        # print('Done processing player data')

    async def send_alert(self, embed):
        channel = discord.utils.get(
            self.bot.get_all_channels(), name=ALERT_CHANNEL_NAME)
        if channel:
            await channel.send(embed=embed)

    def download_and_prepare_thumbnail(self, image_url, output_path="thumbnail.png"):
        # Step 1: Download the image
        headers = {'User-Agent': 'PostmanRuntime/7.44.0'}
        response = requests.get(image_url, headers=headers)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGBA")

        # Step 2: Resize while keeping aspect ratio (shortest side = 80px)
        w, h = img.size
        if w < h:
            new_w = 1000
            new_h = int(h * (1000 / w))
        else:
            new_h = 1000
            new_w = int(w * (1000 / h))
        img = img.resize((new_w, new_h), Image.NEAREST)

        # Step 3: Crop to center 80x80
        left = (new_w - 1000) // 2
        top = (new_h - 1000) // 2
        img = img.crop((left, top, left + 1000, top + 1000))

        # Step 4: Save the output
        img.save(output_path)
        print(f"Thumbnail saved to {output_path}")

    @tasks.loop(seconds=CHECK_INTERVAL)
    async def check_realm(self):
        # print('Getting current player data')
        minecraft_data = load_minecraft_data()
        if 'realm_uhs' not in minecraft_data or minecraft_data['realm_uhs'] == '':
            minecraft_data = self.reauthenticate('https://pocket.realms.minecraft.net/')
        url = f"https://pocket.realms.minecraft.net/worlds/{REALM_ID}"
        running = True
        while(running):
            running = False
            headers = {
                'Authorization': f'XBL3.0 x={minecraft_data["realm_uhs"]};{minecraft_data["realm_token"]}',
                'User-Agent': 'MCPE/UWP',
                'Client-Version': '1.21.84',
                'Host': 'pocket.realms.minecraft.net'
            }
            response = requests.get(url, headers=headers)

            # print("Status Code", response.status_code)
            if response.status_code == 401:
                print('Reauthenticating at check_realm')
                running = True
                minecraft_data = self.reauthenticate('https://pocket.realms.minecraft.net/')
                continue
            elif response.status_code == 200:
                response_json = response.json()
                minecraft_data['current_player_data'] = response_json['players']
                save_minecraft_data(minecraft_data)
                # print('Got current player data')
                await self.process_player_data()
            else:
                print(response)

    @check_realm.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="test_minecraft",
                          description="Test")
    async def test_minecraft(self, interaction: discord.Interaction):
        self.download_and_prepare_thumbnail('https://minecraft.wiki/images/DefeatEnderdragon-23b82.png?09d3c', 'thumbnail.png')

        embed = discord.Embed(
            title="<player> defeated the Ender Dragon!... again",
            description='Successfully respawn and defeat the ender dragon',
            color=0xFFC107,
            timestamp=datetime.now()
        )
        file = discord.File("thumbnail.png", filename="thumbnail.png")
        embed.set_thumbnail(url="attachment://thumbnail.png")
        embed.set_footer(text="Minecraft Realm Tracker")
        await interaction.response.send_message(
            file=file,
            embed=embed,
            ephemeral=True)


async def setup(bot):
    await bot.add_cog(RealmTracker(bot))
