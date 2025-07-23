import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from parser import Parser, Player

class DataCache:
    def __init__(self):
        self.current_month_data: List[Player] = []
        self.previous_month_data: List[Player] = []
        self.last_update: Optional[datetime] = None
        self.is_updating = False
        
    async def update_data(self):
        """Оновлює кешовані дані з API"""
        if self.is_updating:
            print("Data update already in progress, skipping...")
            return
            
        self.is_updating = True
        print(f"Starting data update at {datetime.now(timezone.utc)}")
        
        try:
            parser = Parser()
            
            # Отримуємо дані поточного місяця
            print("Fetching current month data...")
            current_data = await parser.fetch_and_parse_leaderboard(is_admin=True, is_current_month=True)
            if current_data:
                self.current_month_data = current_data
                print(f"Updated current month data: {len(current_data)} players")
            
            # Отримуємо дані попереднього місяця
            print("Fetching previous month data...")
            previous_data = await parser.fetch_and_parse_leaderboard(is_admin=True, is_current_month=False)
            if previous_data:
                self.previous_month_data = previous_data
                print(f"Updated previous month data: {len(previous_data)} players")
            
            self.last_update = datetime.now(timezone.utc)
            print(f"Data update completed at {self.last_update}")
            
        except Exception as e:
            print(f"Error during data update: {e}")
        finally:
            self.is_updating = False
    
    def get_current_month_data(self, with_steam_id: bool = False) -> List[Player]:
        """Повертає дані поточного місяця"""
        if with_steam_id:
            return self.current_month_data
        else:
            # Повертаємо копію без Steam ID для публічних команд
            return [Player(p.name, p.id, p.value) for p in self.current_month_data]
    
    def get_previous_month_data(self) -> List[Player]:
        """Повертає дані попереднього місяця"""
        return self.previous_month_data
    
    def is_data_fresh(self, max_age_minutes: int = 15) -> bool:
        """Перевіряє чи дані свіжі"""
        if not self.last_update:
            return False
        
        age = datetime.now(timezone.utc) - self.last_update
        return age.total_seconds() < (max_age_minutes * 60)
    
    def get_cache_status(self) -> str:
        """Повертає статус кешу"""
        if not self.last_update:
            return "🦍 Дані не шось завантажені"
        
        age = datetime.now(timezone.utc) - self.last_update
        age_minutes = int(age.total_seconds() / 60)
        
        status = "🦍 Свіжі" if self.is_data_fresh() else "🦍 не такі уж і свіжі"
        current_count = len(self.current_month_data)
        previous_count = len(self.previous_month_data)
        
        return f"{status} (оновлено {age_minutes} хв тому)\n📊 Поточний місяць: {current_count} гравців\n📊 Попередній місяць: {previous_count} гравців"

# Глобальний екземпляр кешу
data_cache = DataCache()
