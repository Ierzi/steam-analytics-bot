import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from steam import Steam
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


# Commands
@bot.tree.command(name="getownedgames", description="Get someone's owned games.")
@app_commands.describe(steamid="The SteamID to get the information from")
async def get_owned_games(interaction: discord.Interaction, steamid: int):
    await interaction.response.defer()
    summary = await steam.get_player_summaries(steamid)
    console.print(summary)
    await interaction.followup.send("check console")


if __name__ == "__main__":
    bot.run(TOKEN)