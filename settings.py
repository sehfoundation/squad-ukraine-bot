import os
from typing import List

class Settings:
    TOKEN_BM = os.getenv('TOKEN_BM', '')  # Battlemetrics API token
    TOKEN_BOT = os.getenv('TOKEN_BOT', '')  # Discord bot token
    SERVER_ID_SQ_1 = 30985204
    SERVER_ID_SQ_2 = 31020814
    
    # Список Discord ID користувачів які можуть використовувати ВСІ команди (окрім randomsquadname)
    ALLOWED_USER_IDS: List[int] = [
        1344598543440019538,
        333565316372365313,
        721996501999550485,
        1379412359663325205,
        1397901457012822018
    ]
    
    # Канал для автоматичних оновлень топу (встановіть ID каналу)
    AUTO_UPDATE_CHANNEL_ID = None  # Замініть на ID каналу де хочете автооновлення
    
    # Інтервал оновлення даних (в секундах)
    DATA_UPDATE_INTERVAL = 600  # 10 хвилин
