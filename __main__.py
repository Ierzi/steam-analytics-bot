import discord
from discord import Colour, Embed, app_commands
from discord.ext import commands
import asyncio
from utils.steam import Steam
from utils.functions import to_timestamp
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

# Types
class Colors:
    STEAM_BLUE = 44526


# Test guild
TEST_GUILD = 1408027216733933639

# Commands
@bot.tree.command(name="getplayersummary", description="Get someone's player summary.")
@app_commands.describe(steamid="The SteamID to get the summary from.")
async def get_player_summary(interaction: discord.Interaction, steamid: str):
    await interaction.response.defer()
    summary = await steam.get_player_summaries(int(steamid))
    
    # OUTPUT FORMAT
    # {
    #     'response': {
    #         'players': [
    #             {
    #                 'steamid': '76561199346451696',
    #                 'communityvisibilitystate': 3,
    #                 'profilestate': 1,
    #                 'personaname': 'Ierzi',
    #                 'commentpermission': 1,
    #                 'profileurl': 'https://steamcommunity.com/id/Ierzi/',
    #                 'avatar': 'https://avatars.steamstatic.com/a688725d2b03b596e5f9dd7c0ba56073b711fdcf.jpg',
    #                 'avatarmedium': 'https://avatars.steamstatic.com/a688725d2b03b596e5f9dd7c0ba56073b711fdcf_medium.jpg',
    #                 'avatarfull': 'https://avatars.steamstatic.com/a688725d2b03b596e5f9dd7c0ba56073b711fdcf_full.jpg',
    #                 'avatarhash': 'a688725d2b03b596e5f9dd7c0ba56073b711fdcf',
    #                 'lastlogoff': 1760735439,
    #                 'personastate': 1,
    #                 'realname': 'Ierzi',
    #                 'primaryclanid': '103582791429521408',
    #                 'timecreated': 1655635901,
    #                 'personastateflags': 0,
    #                 'loccountrycode': 'FR'
    #             }
    #         ]
    #     }
    # }

    # We dont need allat
    player_summary: dict = summary['response']['players'][0] # Request only returns one player, so index 0

    # Get useful info
    steam_id = player_summary.get("steamid")
    name = player_summary.get("personaname")
    profile_url = player_summary.get("profileurl")
    avatar = player_summary.get("avatar") # For embed image
    last_online = int(player_summary.get("lastlogoff"))
    created_timestamp = int(player_summary.get("timecreated"))
    country_code: str = player_summary.get("loccountrycode")

    # Format it to an embed
    title = f"{name} :flag_{country_code.lower()}:" # Should convert the country code to a flag emoji
    summary_embed = Embed(
        colour=Colors.STEAM_BLUE,
        title=title,
    )

    summary_embed = summary_embed.set_thumbnail(url=avatar)
    summary_embed = summary_embed.add_field(name="Steam ID", value=steam_id)
    relative_last_online = to_timestamp(last_online, 'R')
    summary_embed = summary_embed.add_field(name="Last Online", value=f"Last online {relative_last_online}")
    long_date_created = to_timestamp(created_timestamp, 'D')
    relative_created = to_timestamp(created_timestamp, 'R')
    summary_embed = summary_embed.add_field(name="Created",  value=f"Created {relative_created} ({long_date_created})")
    summary_embed = summary_embed.add_field(name="URL", value=profile_url)

    # Send final message
    await interaction.followup.send(embed=summary_embed)

# Events
@bot.event
async def on_ready():
    # guild = discord.Object(TEST_GUILD)
    console.print(f"Logged in as {bot.user}")

    # Sync commands
    synced = await bot.tree.sync()
    console.print(f"Synced {len(synced)} commands")


if __name__ == "__main__":
    bot.run(TOKEN)