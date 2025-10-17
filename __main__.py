import discord
from discord.ext import commands
import asyncio
from aiosteam_api import Steam
import os
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
STEAM_KEY = os.getenv("STEAM_KEY")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
    allowed_mentions=discord.AllowedMentions.none()
)

steam = Steam(STEAM_KEY)

console = Console()

# Events
@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    console.print(f"Synced {len(synced)} commands")
    console.print(f"Logged in as {bot.user}")

if __name__ == "__main__":
    bot.run(TOKEN)