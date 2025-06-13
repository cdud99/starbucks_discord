# cogs/drink.py
import random
import discord
from discord import app_commands
from discord.ext import commands


class Frap(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="drink",
                          description="Get a sassy drink suggestion")
    @app_commands.default_permissions()
    async def drink(self, interaction: discord.Interaction):
        drinks = [
            "Venti Caramel Frappuccino with whipped cream and extra guilt",
            "Tall Matcha Frap with oat milk and existential dread",
            "Grande Mocha Cookie Crumble Frap — because you deserve it… allegedly",
            "Short Espresso Frap because your will to live is also short",
            "Venti Pink Drink disguised as confidence",
            "Trenta Frap with 13 pumps of sugar and a side of regret",
            "Grande Vanilla Bean Frap — sweet, basic, and emotionally unavailable",
            "Tall Java Chip Frap: The official drink of chaos goblins",
            "Grande Strawberry Frap: Served with a plastic smile",
            "Double shot of espresso in a Frap cup just to confuse people",
            "Unicorn Frap: tastes like cotton candy and crushed dreams",
            "Caramel Ribbon Crunch with enough drizzle to drown your trauma",
            "Chai Creme Frap for the person who reads horoscopes religiously",
            "Triple blended mocha with ‘trauma’ spelled in caramel on the lid",
            "Strawberry Açaí Refresher, but somehow it’s beige",
            "Green Tea Frap that’s 90%% syrup and 10%% self-control",
            "Decaf Frap — for when you’ve given up on life *and* caffeine",
            "Iced White Mocha in a blender with 12 pumps of entitlement",
            "Frappuccino with no ice, no milk, and no point",
            "Frap with every topping on the bar because why not burn it down?",
            "A secret menu drink made by Satan during a rush",
            "Hot Chocolate Frap — because we needed one more contradiction",
            "Pumpkin Spice Frap in June. Because chaos knows no season",
            "Frap with almond milk, no whip, 17 pumps of 'why me?'",
            "Cookies and Cream Frap topped with your poor decisions",
            "Cold Brew poured over crushed Frap just to start a war",
            "A completely blended birthday cake, wrapper and all",
            "S’mores Frap with a spark of childhood trauma",
            "Mango Dragonfruit Refresher blended and filled with regret",
            "Frap with a shot of espresso, a shot of tequila, and a therapist",
            "Butterbeer Frap that thinks it's still cool in 2025",
            "Blended Iced Coffee with your tears from today's shift",
            "Peach Green Tea Frap, bitter like your last relationship",
            "Mocha Frap, two shots of espresso, one missed therapy appointment",
            "Peppermint Frap in summer — because you’re festive and unhinged",
            "No whip, no base, no soul. Just vibes.",
            "Syrup Frap — just a cup of caramel with a green straw",
            "Double chocolate chip Frap, but every chip is passive aggression",
            "Salted caramel Frap topped with management's empty promises",
            "Espresso blended with deadlines and broken mobile orders",
            "Oatmilk Frap, because cow milk is too emotionally intense",
            "Frozen matcha blended with your manager’s lies",
            "Frappuccino made with tears of the last barista who asked for a raise",
            "Blended dragonfruit and spite — the shift supervisor’s special",
            "Grande Frap that’s 10%% coffee, 90%% coping mechanism",
            "Pink Drink blended and served with a passive-aggressive straw",
            "Syrup and ice in a blender: the Karen Special",
            "Frappuccino labeled 'Chris' even though your name is Sarah",
            "A Java Chip with extra whip and no remorse",
            "Your favorite drink but made wrong just like your life choices",
            "Secret menu Frap with a side of job application to Dutch Bros",
        ]
        await interaction.response.send_message(
            f"☕ Your drink is: **{random.choice(drinks)}**")


async def setup(bot: commands.Bot):
    await bot.add_cog(Frap(bot))
