from typing import Any, Iterable, Literal, Optional, overload, Union
import aiohttp
import asyncio

class Steam:
    """An actual async-friendly steam API cause the other ones suck"""
    _BASE_URL = "http://api.steampowered.com/"
    _STORE_URL = "https://store.steampowered.com/api/" # Fetch info about games (semi-supported)

    def __init__(self, 
        api_key: str, 
        *, 
        headers: dict[str, str] = None, 
        default_language: str = "en",
        default_country_code: str = None
    ) -> None:
        self._api_key = api_key
        self._headers = headers
        self._default_language = default_language
        self._default_country_code = default_country_code
    
    async def _get(
        self,
        *,
        url_type: Literal["BASE_URL", "STORE_URL"],
        endpoint: str,
        params: dict[str, Any] = {},
        require_api_key: bool = False
    ) -> dict:
        full_url = f"{self._BASE_URL if url_type == 'BASE_URL' else self._STORE_URL}{endpoint}"
        if require_api_key:
            params['key'] = self._api_key

        params['format'] = 'json'
        async with aiohttp.ClientSession() as session:
            async with session.get(full_url, params=params, headers=self._headers) as response:
                response.raise_for_status()
                return await response.json()
    
    async def get_news_for_app(self, app_id: str, count: int = 3, maxlength: int = 300):
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
    
    async def get_global_achievement_percentages_for_app(self, game_id: str):
        """Returns on global achievements overview of a specific game in percentages. """
        return await self._get(
            url_type="BASE_URL",
            endpoint="ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/",
            params={
                "gameid": game_id
            }
        )

    @overload
    async def get_player_summaries(self, steam_id: str) -> dict: ...

    @overload
    async def get_player_summaries(self, steam_id: Iterable[str]) -> dict: ...

    async def get_player_summaries(self, steam_id: Union[str, Iterable[str]]) -> dict:
        """Returns basic profile information for a single or a list of 64-bit Steam IDs."""
        if isinstance(steam_id, int):
            return await self._get(
                url_type="BASE_URL",
                endpoint="/ISteamUser/GetPlayerSummaries/v0002/",
                params={
                    "steamids": steam_id
                },
                require_api_key=True
            )
        else:
            return await self._get(
                url_type="BASE_URL",
                endpoint="/ISteamUser/GetPlayerSummaries/v0002/",
                params={
                    "steamids": ",".join(steam_id)
                },
                require_api_key=True
            )
    
    async def get_friend_list(self, steam_id: str, relationship_filter: Literal["all", "friend"] = "all"):
        """Returns the friend list of any Steam user, provided their Steam Community profile visibility is set to Public."""
        return await self._get(
            url_type="BASE_URL",
            endpoint="/ISteamUser/GetFriendList/v0001/",
            params={
                "steamid": steam_id,
                "relationship": relationship_filter
            },
            require_api_key=True
        )
    
    async def get_player_achievements(self, steam_id: str, app_id: str, language: Optional[str] = None):
        """Returns a list of achievements for this user by app ID. If language is None, use default language."""
        params = {
                "steamid": steam_id,
                "appid": app_id
        }
        params['l'] = language if language else self._default_language

        return await self._get(
            url_type="BASE_URL",
            endpoint="ISteamUserStats/GetPlayerAchievements/v0001/",
            params=params,
            require_api_key=True
        )
    
    async def get_owned_games(self, steam_id: str, *, include_appinfo: bool = False, include_played_free_games: bool = False):
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
            params=params,
            require_api_key=True
        )

    async def get_recently_played_games(self, steam_id: str, count: Optional[int] = None):
        """Returns a list of games a player has played in the last two weeks, if the profile is publicly visible."""
        params = {
            "steamid": steam_id
        }
        if count:
            params['count'] = count
        
        return await self._get(
            url_type="BASE_URL",
            endpoint="IPlayerService/GetRecentlyPlayedGames/v0001/",
            params=params,
            require_api_key=True
        )
    
    async def get_schema_for_game(self, app_id: str, language: Optional[str] = None):
        """Get detailed game info by AppID."""
        params  = {
            "appid": app_id
        }
        params['l'] = language if language else self._default_language

        return await self._get(
            url_type="BASE_URL",
            endpoint="ISteamUserStats/GetSchemaForGame/v2",
            params=params,
            require_api_key=True
        )
        
    # STORE API REQUESTS
    @overload
    async def app_details(self, app_id: str, country_code: Optional[str] = None, language: Optional[str] = None): ...

    @overload
    async def app_details(self, app_id: Iterable[str], country_code: Optional[str] = None, language: Optional[str] = None): ...

    async def app_details(self, app_id: Union[str, Iterable[str]], country_code: Optional[str] = None, language: Optional[str] = None):
        """Returns information about Steam games by their AppID."""
        params = {
            "appids": app_id if isinstance(app_id, int) else ",".join(app_id)
        }
        if country_code:
            params['cc'] = country_code
        elif self._default_country_code:
            params['cc'] = self._default_country_code
        else:
            # cc is an optional argument
            pass

        params['l'] = language if language else self._default_language
        
        return await self._get(
            url_type="STORE_URL",
            endpoint="appdetails/",
            params=params
        )

    async def store_search(self, term: str, country_code: Optional[str] = None, language: Optional[str] = None):
        """Searches the Steam store for games by search term."""
        search_words = term.split()
        search = "+".join(search_words)

        params = {
            "term": search
        }

        # Steam Store search API requires cc parameter to work properly
        if country_code:
            params['cc'] = country_code
        elif self._default_country_code:
            params['cc'] = self._default_country_code
        else:
            # Default to US if no country code is specified
            params['cc'] = 'us'
            
        params['l'] = language if language else self._default_language

        return await self._get(
            url_type="STORE_URL",
            endpoint="storesearch/",
            params=params
        )
    
    async def featured_categories(self): # wow no arguments
        """Get featured games, top sellers, new releases and specials"""
        return await self._get(
            url_type="STORE_URL",
            endpoint="featuredcategories/"
        )