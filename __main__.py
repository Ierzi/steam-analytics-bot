import discord
from discord import Interaction, Embed, app_commands
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
async def get_player_summary(interaction: Interaction, steamid: str):
    await interaction.response.defer()
    summary = await steam.get_player_summaries(steamid)
    
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
    avatar = player_summary.get("avatarfull") # For embed image
    last_online = int(player_summary.get("lastlogoff"))
    created_timestamp = int(player_summary.get("timecreated"))
    country_code: str = player_summary.get("loccountrycode")

    # Format it to an embed
    title = f"{name} - :flag_{country_code.lower()}:" # Should convert the country code to a flag emoji
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

@bot.tree.command(name="getfriendlist", description="Get someone's friend list.")
@app_commands.describe(steamid="The SteamID to get the friend list from.")
async def get_friend_list(interaction: Interaction, steamid: str):
    # Helper commands
    async def get_username(steamid: str) -> str:
        data = await steam.get_player_summaries(steamid)
        return data['response']['players'][0]['personaname']


    await interaction.response.defer()
    response = await steam.get_friend_list(steamid)

    # OUTPUT FORMAT
    # {
    #     'friendslist': {
    #         'friends': [
    #             {'steamid': '76561198985638489', 'relationship': 'friend', 'friend_since': 1731959988},
    #             {'steamid': '76561199204710322', 'relationship': 'friend', 'friend_since': 1732377864},
    #             {'steamid': '76561199209323472', 'relationship': 'friend', 'friend_since': 1750702559},
    #             {'steamid': '76561199214689897', 'relationship': 'friend', 'friend_since': 1750931217},
    #             {'steamid': '76561199216328722', 'relationship': 'friend', 'friend_since': 1729787388},
    #             {'steamid': '76561199250750557', 'relationship': 'friend', 'friend_since': 1732156051},
    #             {'steamid': '76561199389575166', 'relationship': 'friend', 'friend_since': 1753898284},
    #             {'steamid': '76561199489356195', 'relationship': 'friend', 'friend_since': 1738978669},
    #             {'steamid': '76561199542646800', 'relationship': 'friend', 'friend_since': 1736083166},
    #             {'steamid': '76561199557878979', 'relationship': 'friend', 'friend_since': 1732895138},
    #             {'steamid': '76561199557946169', 'relationship': 'friend', 'friend_since': 1750961383},
    #             {'steamid': '76561199558836623', 'relationship': 'friend', 'friend_since': 1722853473},
    #             {'steamid': '76561199559614779', 'relationship': 'friend', 'friend_since': 1753269279},
    #             {'steamid': '76561199638368311', 'relationship': 'friend', 'friend_since': 1736070175},
    #             {'steamid': '76561199686591093', 'relationship': 'friend', 'friend_since': 1724417688}
    #         ]
    #     }
    # }

    friends: list[dict] = response['friendslist']['friends']
    formatted_data = []  # Tuple  -> (username, relative timestamp)
    for friend in friends:
        username = await get_username(friend.get('steamid'))
        relative_timestamp = to_timestamp(int(friend.get('friend_since')), 'R')
        formatted_data.append((username, relative_timestamp))\
    
    friend_list_username = await get_username(steamid)

    friend_list_embed = Embed(
        colour=Colors.STEAM_BLUE,
        title=f"{friend_list_username}'s friends",
        description=""
    )
    str_formatted = [f"{u} - {friend_since}" for u, friend_since in formatted_data]
    friend_list_embed.description += "\n".join(str_formatted)
    
    await interaction.followup.send(embed=friend_list_embed)


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