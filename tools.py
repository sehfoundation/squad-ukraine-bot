from datetime import datetime, timezone
import calendar

class Tools:
    @staticmethod
    def get_period() -> str:
        """Повертає період для поточного місяця у форматі ISO 8601"""
        now = datetime.now(timezone.utc)
        first_day_of_month = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        start_date_str = first_day_of_month.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_date_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return f"{start_date_str}:{end_date_str}"
    
    @staticmethod
    def get_previous_month_period() -> str:
        """Повертає період для попереднього місяця у форматі ISO 8601"""
        now = datetime.now(timezone.utc)
        
        # Отримуємо перший день поточного місяця
        first_day_of_current_month = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        # Віднімаємо один день щоб отримати останній день попереднього місяця
        if now.month == 1:
            last_day_of_previous_month = datetime(now.year - 1, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
            first_day_of_previous_month = datetime(now.year - 1, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        else:
            # Отримуємо кількість днів у попередньому місяці
            days_in_previous_month = calendar.monthrange(now.year if now.month > 1 else now.year - 1, 
                                                        now.month - 1 if now.month > 1 else 12)[1]
            last_day_of_previous_month = datetime(now.year if now.month > 1 else now.year - 1, 
                                                now.month - 1 if now.month > 1 else 12, 
                                                days_in_previous_month, 23, 59, 59, tzinfo=timezone.utc)
            first_day_of_previous_month = datetime(now.year if now.month > 1 else now.year - 1, 
                                                 now.month - 1 if now.month > 1 else 12, 
                                                 1, 0, 0, 0, tzinfo=timezone.utc)
        
        start_date_str = first_day_of_previous_month.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_date_str = last_day_of_previous_month.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return f"{start_date_str}:{end_date_str}"
    
    @staticmethod
    def format_time(seconds: int) -> str:
        """Форматує час у секундах в формат 1d 2h 3m 4s"""
        days = seconds // (24 * 3600)
        hours = (seconds % (24 * 3600)) // 3600
        minutes = (seconds % 3600) // 60
        sec = seconds % 60
        
        return f"{days}d {hours}h {minutes}m {sec}s"
