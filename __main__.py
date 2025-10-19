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
    DARK_STEAM_BLUE = 1779768

# Test guild
TEST_GUILD = 1408027216733933639

# Helper functions
async def get_username(steamid: str) -> str:
    data = await steam.get_player_summaries(steamid)
    players = data['response']['players']
    if not players:
        raise ValueError(f"No player found with Steam ID: {steamid}")
    return players[0]['personaname']

# Commands
@bot.tree.command(name=f"getplayersummary", description="Get someone's player summary.")
@app_commands.describe(steamid="The SteamID to get the summary from.")
async def get_player_summary(interaction: Interaction, steamid: str):
    await interaction.response.defer()
    summary = await steam.get_player_summaries(steamid.strip())
    console.print(summary)
    
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

@bot.tree.command(name="getrecentlyplayedgames", description="Get someone's recently played games if their profile aint private.")
@app_commands.describe(steamid="The SteamID to get the recently played games from.")
async def get_recently_played_games(interaction: Interaction, steamid: str):
    await interaction.response.defer()
    response = await steam.get_recently_played_games(steamid)
    
    # OUTPUT FORMAT
    # {
    #     'response': {
    #         'total_count': 5,
    #         'games': [
    #             {
    #                 'appid': 322170,
    #                 'name': 'Geometry Dash',
    #                 'playtime_2weeks': 559,
    #                 'playtime_forever': 49556,
    #                 'img_icon_url': '7fb2e71773468dbd98d56c733b604c92f5ab0ad4',
    #                 'playtime_windows_forever': 49209,
    #                 'playtime_mac_forever': 347,
    #                 'playtime_linux_forever': 0,
    #                 'playtime_deck_forever': 0
    #             },
    #             {
    #                 'appid': 504230,
    #                 'name': 'Celeste',
    #                 'playtime_2weeks': 326,
    #                 'playtime_forever': 5229,
    #                 'img_icon_url': '04cb7aa0b497a3962e6b1655b7fd81a2cc95d18b',
    #                 'playtime_windows_forever': 5229,
    #                 'playtime_mac_forever': 0,
    #                 'playtime_linux_forever': 0,
    #                 'playtime_deck_forever': 0
    #             },
    #             {
    #                 'appid': 391540,
    #                 'name': 'Undertale',
    #                 'playtime_2weeks': 72,
    #                 'playtime_forever': 509,
    #                 'img_icon_url': '2ce672b89b63ec1e70d2f12862e72eb4a33e9268',
    #                 'playtime_windows_forever': 509,
    #                 'playtime_mac_forever': 0,
    #                 'playtime_linux_forever': 0,
    #                 'playtime_deck_forever': 0
    #             },
    #             {
    #                 'appid': 945360,
    #                 'name': 'Among Us',
    #                 'playtime_2weeks': 49,
    #                 'playtime_forever': 338,
    #                 'img_icon_url': 'b82c3f46da8f3c918e1c9e0d18bd6fa8fcef6801',
    #                 'playtime_windows_forever': 338,
    #                 'playtime_mac_forever': 0,
    #                 'playtime_linux_forever': 0,
    #                 'playtime_deck_forever': 0
    #             },
    #             {
    #                 'appid': 460920,
    #                 'name': 'Steep',
    #                 'playtime_2weeks': 41,
    #                 'playtime_forever': 234,
    #                 'img_icon_url': '0cd871768bc488856bd5bf44a196b221fc9a878b',
    #                 'playtime_windows_forever': 234,
    #                 'playtime_mac_forever': 0,
    #                 'playtime_linux_forever': 0,
    #                 'playtime_deck_forever': 0
    #             }
    #         ]
    #     }
    # }

    games: list[dict] = response['response']['games']
    game_data = [] # directly formatted as a str
    for game in games:
        game_name = game.get("name")
        game_playtime_2w = round(int(game.get("playtime_2weeks", 0)) / 60, 2)  # Hours
        game_total_playtime = round(int(game.get("playtime_forever", 0)) / 60, 2) # Hours
        string = f"**{game_name}** - {game_playtime_2w}/{game_total_playtime} hours"
        game_data.append(string)
    
    username = await get_username(steamid)
    rpg_embed = Embed(
        colour=Colors.STEAM_BLUE,
        title=f"{username}'s Steam Games",
        description=""
    )

    rpg_embed.description += "\n".join(game_data)

    await interaction.followup.send(embed=rpg_embed)
    
@bot.tree.command(name="currentlyplaying", description="Get someone's currently playing game if their profile is not private.")
@app_commands.describe(steamid="SteamID (kinda lazy to put a description)")
async def get_currently_playing(interaction: Interaction, steamid: str):
    await interaction.response.defer()
    summary = await steam.get_player_summaries(steamid)
    # See above for format
    player_summary: dict = summary['response']['players'][0]

    currently_playing = player_summary.get("gameextrainfo", False)
    username = player_summary.get("personaname")
        
    if currently_playing:
        await interaction.followup.send(f"{username} is currently playing **{currently_playing}**")
        return

    await interaction.followup.send(f"{username} aint playing anything.")


@bot.tree.command(name="search", description="Search the Steam Store for games by the search term.")
@app_commands.describe(term="The term to search.")
async def search(interaction: Interaction, term: str):
    await interaction.response.defer()

    response = await steam.store_search(term)
    
    if response['total'] == 0:
        await interaction.followup.send(f'No games found for "{term}"')
        return
    
    # Create embed for search results
    search_embed = Embed(
        colour=Colors.STEAM_BLUE,
        title=f'Search results for "{term}"',
        description=f"Found {response['total']} games"
    )
    
    # Add games to embed
    for i, game in enumerate(response['items'][:10]):
        game_name = game['name']
        app_id = game['id']
        store_url = f"https://store.steampowered.com/app/{app_id}/"
        
        # Truncate long game names
        if len(game_name) > 250:
            game_name = game_name[:250] + "..."
        
        search_embed.add_field(
            name=f"{i+1}. {game_name}",
            value=f"[Store Page]({store_url})",
            inline=False
        )
    
    await interaction.followup.send(embed=search_embed)


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