from typing import Any, Literal, Optional, overload, Union
import aiohttp
import asyncio

class Steam:
    """An actual async-friendly steam API cause the other ones suck"""
    BASE_URL = "http://api.steampowered.com/"
    STORE_URL = "https://store.steampowered.com/api/"

    def __init__(self, 
        api_key: str, 
        *, 
        headers: dict[str, str] = None, 
        default_language: str = "en"
    ) -> None:
        self.api_key = api_key
        self.headers = headers
        self.default_langauge = default_language
    
    async def _get(
        self,
        *,
        url_type: Literal["BASE_URL", "STORE_URL"],
        endpoint: str,
        params: dict[str, Any] = {}
    ) -> dict:
        full_url = f"{self.BASE_URL if url_type == 'BASE_URL' else self.STORE_URL}{endpoint}"
        params['key'] = self.api_key
        params['format'] = 'json'
        async with aiohttp.ClientSession() as session:
            async with session.get(full_url, params=params, headers=self.headers) as response:
                response.raise_for_status()
                return await response.json()
    
    async def get_news_for_app(self, app_id: int, count: int = 3, maxlength: int = 300):
        """Returns the latest of a game specified by its appID."""
        return await self._get(
            url_type="BASE_URL",
            endpoint="ISteamNews/GetNewsForApp/v0002/",
            params={
                "appid": app_id,
                "count": count,
                "maxlength": maxlength
            }
        )
    
    async def get_global_achievement_percentages_for_app(self, game_id: int):
        """Returns on global achievements overview of a specific game in percentages. """
        return await self._get(
            url_type="BASE_URL",
            endpoint="ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/",
            params={
                "gameid": game_id
            }
        )

    @overload
    async def get_player_summaries(self, steam_id: int) -> dict: ...

    @overload
    async def get_player_summaries(self, steam_id: list[int]) -> dict: ...

    async def get_player_summaries(self, steam_id: Union[int, list[int]]) -> dict:
        """Returns basic profile information for a single or a list of 64-bit Steam IDs."""
        if isinstance(steam_id, int):
            return await self._get(
                url_type="BASE_URL",
                endpoint="/ISteamUser/GetPlayerSummaries/v0002/",
                params={
                    "steamids": steam_id
                }
            )
        else:
            return await self._get(
                url_type="BASE_URL",
                endpoint="/ISteamUser/GetPlayerSummaries/v0002/",
                params={
                    "steamids": ",".join(steam_id)
                }
            )
    
    async def get_friend_list(self, steam_id: int, relationship_filter: Literal["all", "friend"]):
        """Returns the friend list of any Steam user, provided their Steam Community profile visibility is set to Public."""
        return await self._get(
            url_type="BASE_URL",
            endpoint="/ISteamUser/GetFriendList/v0001/",
            params={
                "steamid": steam_id,
                "relationship": relationship_filter
            }
        )
    
    async def get_player_achievements(self, steam_id: int, app_id: int, language: Optional[str] = None):
        """Returns a list of achievements for this user by app ID. If language is None, use default language."""
        params = {
                "steamid": steam_id,
                "appid": app_id
        }
        params['l'] = language if language else self.default_langauge

        return await self._get(
            url_type="BASE_URL",
            endpoint="ISteamUserStats/GetPlayerAchievements/v0001/",
            params=params
        )
    
    async def get_owned_games(self, steam_id: int, *, include_appinfo: bool = False, include_played_free_games: bool = False):
        """
        Returns a list of games a player owns along with some playtime information, if the profile is publicly visible. 
        
        Private, friends-only, and other privacy settings are not supported unless you are asking for your own personal details 
        (ie the WebAPI key you are using is linked to the steamid you are requesting). 

        Arguements:
            steam_id: The SteamID of the account.
            include_appinfo: Include game name and logo information in the output. The default is to return appids only.
            include_played_free_games: By default, free games like Team Fortress 2 are excluded (as technically everyone owns them). If include_played_free_games is set, they will be returned if the player has played them at some point. 
        
        """

        # Parse optional arguments
        params = {
            "steamid": steam_id
        }
        if include_appinfo:
            params['include_appinfo'] = True
        if include_played_free_games:
            params['include_played_free_games'] = True
        
        return await self._get(
            url_type="BASE_URL",
            endpoint="IPlayerService/GetOwnedGames/v0001/",
            params=params
        )
