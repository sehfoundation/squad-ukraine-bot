import aiohttp
import asyncio
import os
from typing import List, Dict, Any
from settings import Settings
from tools import Tools

class Player:
    def __init__(self, name: str, player_id: int, value: int):
        self.name = name
        self.id = player_id
        self.value = value
        self.steam_id = 0
    
    async def fetch_steam_id(self):
        """Отримує Steam ID гравця з API Battlemetrics"""
        url = f"https://api.battlemetrics.com/players/{self.id}?include=identifier&filter[identifiers]=steamID"
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {Settings.TOKEN_BM}'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        identifiers = data.get('included', [])
                        
                        print(f"Player {self.name} (ID: {self.id}) - found {len(identifiers)} identifiers")
                        
                        for identifier in identifiers:
                            identifier_type = identifier.get('type')
                            attributes = identifier.get('attributes', {})
                            attr_type = attributes.get('type')
                            identifier_value = attributes.get('identifier', '')
                            
                            print(f"  Identifier: type={identifier_type}, attr_type={attr_type}, value={identifier_value}")
                            
                            if (identifier_type == 'identifier' and attr_type == 'steamID'):
                                try:
                                    self.steam_id = int(identifier_value)
                                    print(f"  ✓ Set Steam ID: {self.steam_id}")
                                    break
                                except ValueError:
                                    print(f"  ✗ Could not parse '{identifier_value}' as int")
                        
                        if self.steam_id == 0:
                            print(f"  ✗ No valid Steam ID found for {self.name}")
                    else:
                        print(f"Failed to fetch Steam ID for player {self.id}: HTTP {response.status}")
        except Exception as e:
            print(f"Error fetching Steam ID for player {self.id}: {e}")

class Parser:
    def __init__(self):
        self.settings = Settings()
    
    async def fetch_and_parse_leaderboard(self, is_admin: bool = False, is_current_month: bool = True) -> List[Player]:
        """Отримує і парсить дані лідерборду з серверів"""
        print(f"Starting leaderboard fetch - admin: {is_admin}, current_month: {is_current_month}")
        
        url_sq1 = f"https://api.battlemetrics.com/servers/{Settings.SERVER_ID_SQ_1}/relationships/leaderboards/time"
        url_sq2 = f"https://api.battlemetrics.com/servers/{Settings.SERVER_ID_SQ_2}/relationships/leaderboards/time"
        
        # Збільшуємо page_size щоб отримати більше гравців
        page_size = 200  # Збільшено з 100 до 200
        period = Tools.get_period() if is_current_month else Tools.get_previous_month_period()
        print(f"Period: {period}")
        
        if not Settings.TOKEN_BM:
            print("ERROR: TOKEN_BM is empty!")
            return []
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {Settings.TOKEN_BM}'
        }
        
        params = {
            'page[size]': str(page_size),
            'filter[period]': period
        }
        
        players = []
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                await self._fetch_players_from_server(session, url_sq1, params, headers, players)
                await self._fetch_players_from_server(session, url_sq2, params, headers, players)
            
            print(f"Fetched {len(players)} players before deduplication")
            
            players = await self._remove_duplicate_players(players)
            print(f"After deduplication: {len(players)} players")
            
            if is_admin:
                print("Fetching Steam IDs...")
                await self._fetch_steam_ids_for_players(players)
                print("Steam IDs fetched")
                
                # Підрахуємо скільки Steam ID отримано
                steam_ids_found = sum(1 for p in players if p.steam_id != 0)
                print(f"Steam IDs found: {steam_ids_found}/{len(players)}")
            
            sorted_players = sorted(players, key=lambda x: x.value, reverse=True)
            result = sorted_players[:100]
            print(f"Returning {len(result)} players")
            return result
        
        except Exception as e:
            print(f"Error in fetch_and_parse_leaderboard: {e}")
            return []
    
    async def _fetch_players_from_server(self, session: aiohttp.ClientSession, url: str, 
                                       params: Dict[str, str], headers: Dict[str, str], 
                                       players: List[Player]):
        """Отримує дані гравців з одного сервера"""
        try:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    users = data.get('data', [])
                    
                    for user_data in users:
                        try:
                            player_id = int(user_data.get('id', '0'))
                            name = user_data.get('attributes', {}).get('name', '')
                            value = int(user_data.get('attributes', {}).get('value', '0'))
                            
                            if player_id and name and value:
                                player = Player(name, player_id, value)
                                players.append(player)
                        except (ValueError, TypeError) as e:
                            print(f"Error parsing player data: {e}")
                            continue
                else:
                    print(f"Failed to fetch data from {url}. Status code: {response.status}")
        except Exception as e:
            print(f"Error fetching data from {url}: {e}")
    
    async def _remove_duplicate_players(self, players: List[Player]) -> List[Player]:
        """Видаляє дублікати гравців, сумуючи їх час онлайн"""
        unique_players = {}
        
        for player in players:
            if player.id in unique_players:
                unique_players[player.id].value += player.value
            else:
                unique_players[player.id] = player
        
        return list(unique_players.values())
    
    async def _fetch_steam_ids_for_players(self, players: List[Player]):
        """Отримує Steam ID для всіх гравців з обмеженням запитів"""
        # Зменшуємо затримки та збільшуємо ліміт одночасних запитів
        semaphore = asyncio.Semaphore(50)  # Збільшено з 30 до 50
        
        async def fetch_with_semaphore(player):
            async with semaphore:
                await player.fetch_steam_id()
                await asyncio.sleep(0.05)  # Зменшено затримку з 0.1 до 0.05
        
        # Розбиваємо на батчі по 100 гравців
        batch_size = 100
        for i in range(0, len(players), batch_size):
            batch = players[i:i + batch_size]
            print(f"Processing Steam ID batch {i//batch_size + 1}/{(len(players) + batch_size - 1)//batch_size} ({len(batch)} players)")
            
            tasks = [fetch_with_semaphore(player) for player in batch]
            await asyncio.gather(*tasks)
            
            # Невелика затримка між батчами
            if i + batch_size < len(players):
                await asyncio.sleep(1)
