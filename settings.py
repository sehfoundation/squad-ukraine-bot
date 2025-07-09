import os
from typing import List

class Settings:
    TOKEN_BM = os.getenv('TOKEN_BM', '')  # Battlemetrics API token
    TOKEN_BOT = os.getenv('TOKEN_BOT', '')  # Discord bot token
    SERVER_ID_SQ_1 = 30985204
    SERVER_ID_SQ_2 = 31020814
    
    ADMIN_IDS: List[int] = [
        721996501999550485,
        333565316372365313,
        209329835762253824,
        250745445838487562,
        284011575071866880,
        528240938762502166,
        753980811107106846
    ]
