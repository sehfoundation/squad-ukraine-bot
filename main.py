import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import os
import random
from datetime import datetime, timezone
from dotenv import load_dotenv
from settings import Settings
from tools import Tools
from data_cache import data_cache

load_dotenv()

class SquadBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.none()
        intents.guilds = True
        super().__init__(command_prefix='!', intents=intents)
        self.auto_update_message_id = None
        
    async def setup_hook(self):
        print("Setting up bot...")
        try:
            # Синхронізуємо команди
            print("Syncing commands...")
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} slash commands")
            
            # Виводимо список команд для діагностики
            for command in synced:
                print(f"  - {command.name}: {command.description}")
                
        except Exception as e:
            print(f"Failed to sync commands: {e}")
            import traceback
            traceback.print_exc()
        
        print("Setup hook completed")
        
    async def on_ready(self):
        print(f'🦍 {self.user} has connected to Discord!')
        print(f'🦍 Bot is in {len(self.guilds)} guilds')
        
        # Запускаємо фонові задачі після підключення
        try:
            if not data_updater.is_running():
                print("🦍 Starting data updater...")
                data_updater.start()
            else:
                print("🦍 Data updater already running")
            
            if not auto_update_top.is_running():
                print("🦍 Starting auto update...")
                auto_update_top.start()
            else:
                print("🦍 Auto update already running")
                
            # Ініціалізуємо дані при старті
            print("🦍 Doing initial data update...")
            await data_cache.update_data()
            
        except Exception as e:
            print(f"Error starting background tasks: {e}")
            import traceback
            traceback.print_exc()

bot = SquadBot()

def is_allowed_user():
    """Декоратор для перевірки дозволених користувачів - тільки для спеціальних ID"""
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id in Settings.ALLOWED_USER_IDS
    return app_commands.check(predicate)

# Видаляємо is_admin_user декоратор - більше не потрібен, використовуємо тільки is_allowed_user

@bot.tree.command(name="top", description="Топ 100 онлайн за поточний місяць (нік + час)")
@is_allowed_user()
async def top_command(interaction: discord.Interaction):
    await interaction.response.send_message("🦍 Завантажую дані з кешу, тримайся хлопець...", ephemeral=False)
    
    try:
        players_list = data_cache.get_current_month_data(with_steam_id=False)
        
        if not players_list:
            status = data_cache.get_cache_status()
            await interaction.edit_original_response(content=f"🦍 Немає даних в кеші, щось пішло не так.\n{status}")
            return
        
        embeds = create_leaderboard_embeds(players_list, is_admin=False, title_suffix="")
        
        # Надсилаємо один embed
        await interaction.edit_original_response(content=None, embed=embeds[0])
            
    except Exception as e:
        print(f"Error in top command: {e}")
        await interaction.edit_original_response(content="🦍 Ой, щось зламалось при отриманні даних. Спробуй ще раз!")

@bot.tree.command(name="topad", description="Топ 100 онлайн за поточний місяць (Steam ID + нік + час)")
@is_allowed_user()
async def top_admin_command(interaction: discord.Interaction):
    await interaction.response.send_message("🦍 Завантажую секретні дані з кешу, це тільки для крутих...", ephemeral=True)
    
    try:
        players_list = data_cache.get_current_month_data(with_steam_id=True)
        
        if not players_list:
            status = data_cache.get_cache_status()
            await interaction.edit_original_response(content=f"🦍 Оу, немає даних в кеші, мабуть щось зламалось.\n{status}")
            return
        
        embeds = create_leaderboard_embeds(players_list, is_admin=True, title_suffix="")
        
        # Надсилаємо один embed
        await interaction.edit_original_response(content=None, embed=embeds[0])
            
    except Exception as e:
        print(f"Error in topad command: {e}")
        await interaction.edit_original_response(content="🦍 Йой, щось пішло не так з данними. Попробуй ще раз пізніше!")

@bot.tree.command(name="toppr", description="Топ 100 онлайн за попередній місяць (Steam ID + нік + час)")
@is_allowed_user()
async def top_previous_month_command(interaction: discord.Interaction):
    await interaction.response.send_message("🦍 Шукаю дані старого місяця в кеші, це займе трошки часу...", ephemeral=True)
    
    try:
        players_list = data_cache.get_previous_month_data()
        
        if not players_list:
            status = data_cache.get_cache_status()
            await interaction.edit_original_response(content=f"🦍 Хм, немає даних минулого місяця в кеші, щось не грає.\n{status}")
            return
        
        embeds = create_leaderboard_embeds(players_list, is_admin=True, title_suffix=" (попередній місяць)")
        
        # Надсилаємо один embed
        await interaction.edit_original_response(content=None, embed=embeds[0])
            
    except Exception as e:
        print(f"Error in toppr command: {e}")
        await interaction.edit_original_response(content="🦍 Аяяй, щось не так з данними минулого місяця. Спробуй пізніше!")

@bot.tree.command(name="randomsquadname", description="Генерує випадкову назву для Squad загону")
async def random_squad_name_command(interaction: discord.Interaction):
    # Список прикметників (50 слів)
    adjectives = [
        "Човгаючі", "Чорні", "Коренасті", "Сонливі", "Крихкі", "Середні", "Грайливі",
        "Великі", "Білі", "Швидкі", "Повільні", "Хитрі", "Качьові", "Боязкі",
        "Старі", "Молоді", "Досвідчені", "Імператорські", "Тихі", "Гучні",
        "Терпеливі", "Нетерпеливі", "Гадячські", "Дурні", "Веселі", "Сумні",
        "Злі", "Гачі", "Холодні", "Гарячі", "
        "Голодні", "Ситі", "Втомлені", "Гачі", "Спокійні", "Нервові",
        "Секретні", "Сластиві", "Таємничі", "Очевидні", "Складні", "Прості",
        "Орущі", "Домашні", "Вільні", "Заплутані", "Райдужні", "Випадкові", "Українські", "Вмотивовані", "Заземлені", "Некурящі", "Сомалійські", "Грайливі", "Покоцані", "Відваші види", "Дружелюбні", "Кайдашеві", "Супергачі"
        "Цицькодавні", "Солоненькі", "Меркантильні", "Хуманоїдні"
    ]
    
    # Список іменників у множині (50 слів)
    nouns = [
        "десантники", "карлики", "алконавти", "космодесантники", "депутати", "члени",
        "солдати", "шиншили", "льотчики", "снайпери", "тактикульщики", "вісти",
        "розвідники", "командири", "рядові", "сержанти", "офіцери", "генерали",
        "піхотинці", "артилеристи", "зв'язківці", "водії", "механіки", 
        "сомалійці", "плитовкладачі", "диверсанти", "штурмовики", "гачімени", "нападники",
        "бойовики", "добровольці", "контрактники", "призовники", "резервісти",
        "дюшеси", "крокодили", "цицькодави", "легіонери", "гвардійці", "рейнджери",
        "шоколодки чайка", "сироїди", "миротворці", "патрульні", "собачатники", "полтавці",
        "гренадери", "кавалеристи", "махновці", "зрадойби", "фани телемарафону", "кажаноїди", "корупціонери", "косовити", "українчики", "навуходоносори", "спонсори", "криптошахраї",
        "хейтери бузуглої", "поросята", "порно оператори", "фани Ліверпуля"
    ]
    
    # Обираємо випадкові слова
    random_adjective = random.choice(adjectives)
    random_noun = random.choice(nouns)
    
    # Створюємо назву загону
    squad_name = f"**{random_adjective} {random_noun}**"
    
    # Відповідаємо публічно
    await interaction.response.send_message(
        f"🦍 Випадкова назва Squad загону: {squad_name}",
        ephemeral=False
    )

@bot.tree.command(name="autotop", description="Налаштувати автоматичне оновлення топу в цьому каналі")
@is_allowed_user()
async def auto_top_command(interaction: discord.Interaction):
    await interaction.response.send_message("🦍 Налаштовую автоматичне оновлення топу, це буде круто...", ephemeral=True)
    
    try:
        # Встановлюємо канал для автооновлень
        Settings.AUTO_UPDATE_CHANNEL_ID = interaction.channel.id
        
        # Відправляємо початкове повідомлення
        players_list = data_cache.get_current_month_data(with_steam_id=False)
        if players_list:
            embeds = create_leaderboard_embeds(players_list, is_admin=False, title_suffix=" 🦍")
            message = await interaction.channel.send(embed=embeds[0])
            bot.auto_update_message_id = message.id
            
            await interaction.edit_original_response(
                content=f"🦍 Супер! Автоматичне оновлення топу налаштовано в каналі {interaction.channel.mention}\n"
                        f"🦍 Повідомлення буде оновлюватись кожні 10 хвилин, як годинник!"
            )
        else:
            await interaction.edit_original_response(content="🦍 Оу, немає даних для показу, щось пішло не так")
            
    except Exception as e:
        print(f"Error in autotop command: {e}")
        await interaction.edit_original_response(content="🦍 Ой-ой, щось зламалось при налаштуванні автооновлення")

@bot.tree.command(name="cachestatus", description="Показати статус кешу даних")
@is_allowed_user()
async def cache_status_command(interaction: discord.Interaction):
    status = data_cache.get_cache_status()
    next_update = "Хз коли"
    
    if data_cache.last_update:
        import time
        time_since_update = datetime.now(timezone.utc) - data_cache.last_update
        time_until_next = 600 - time_since_update.total_seconds()  # 600 сек = 10 хв
        if time_until_next > 0:
            next_update = f"{int(time_until_next / 60)} хв {int(time_until_next % 60)} сек"
        else:
            next_update = "Прямо зараз!"
    
    embed = discord.Embed(
        title="🦍 Статус кешу даних",
        description=f"{status}\n\n🦍 Наступне оновлення: {next_update}",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="updatecache", description="Вручну оновити кеш даних")
@is_allowed_user()
async def update_cache_command(interaction: discord.Interaction):
    await interaction.response.send_message("🦍 Починаю оновлювати кеш даних, зачекай хвилинку...", ephemeral=True)
    
    try:
        await data_cache.update_data()
        status = data_cache.get_cache_status()
        await interaction.edit_original_response(content=f"🦍 Кеш оновлено успішно!\n\n{status}")
    except Exception as e:
        print(f"Error in updatecache command: {e}")
        await interaction.edit_original_response(content="🦍 Йой, щось пішло не так при оновленні кешу!")

def create_leaderboard_embeds(players_list, is_admin: bool = False, title_suffix: str = ""):
    """Створює один embed для лідерборду з усіма гравцями"""
    if not players_list:
        return []
    
    # Спробуємо показати всіх 100 гравців
    display_players = players_list[:100]
    
    leaderboard_message = ""
    
    for i, player in enumerate(display_players):
        if is_admin:
            line = f"{i + 1}. **{player.steam_id}** **{player.name}**: {Tools.format_time(player.value)}"
        else:
            line = f"{i + 1}. **{player.name}**: {Tools.format_time(player.value)}"
        
        # Перевіряємо чи не перевищуємо ліміт символів Discord (4096)
        test_message = leaderboard_message + line + "\n"
        if len(test_message) > 4000:  # Залишаємо трохи місця
            remaining_count = len(players_list) - i
            leaderboard_message += f"... та ще {remaining_count} гравців"
            break
        
        leaderboard_message += line + "\n"
    
    embed = discord.Embed(
        title=f"Top 100 Online — SQUAD UKRAINE{title_suffix}",
        description=leaderboard_message,
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )
    
    # Додаємо інформацію про кількість показаних гравців
    actual_shown = min(len(display_players), i + 1) if 'i' in locals() else len(display_players)
    embed.add_field(
        name="🦍 Статистика", 
        value=f"Показано: {actual_shown} з {len(players_list)} гравців", 
        inline=False
    )
    
    if data_cache.last_update:
        embed.set_footer(text=f"🦍 Оновлено: {data_cache.last_update.strftime('%H:%M:%S UTC')}")
    
    return [embed]

@tasks.loop(seconds=Settings.DATA_UPDATE_INTERVAL)
async def data_updater():
    """Фонова задача для оновлення даних кожні 10 хвилин"""
    try:
        print("🦍 Starting scheduled data update...")
        await data_cache.update_data()
    except Exception as e:
        print(f"Error in data updater: {e}")

@tasks.loop(minutes=10)
async def auto_update_top():
    """Фонова задача для автоматичного оновлення топу"""
    try:
        if not Settings.AUTO_UPDATE_CHANNEL_ID or not bot.auto_update_message_id:
            return
        
        channel = bot.get_channel(Settings.AUTO_UPDATE_CHANNEL_ID)
        if not channel:
            return
        
        message = await channel.fetch_message(bot.auto_update_message_id)
        if not message:
            return
        
        players_list = data_cache.get_current_month_data(with_steam_id=False)
        if players_list:
            embeds = create_leaderboard_embeds(players_list, is_admin=False, title_suffix=" 🦍")
            await message.edit(embed=embeds[0])
            print(f"🦍 Auto-updated top message in channel {channel.name}")
        
    except Exception as e:
        print(f"Error in auto update: {e}")

@data_updater.before_loop
async def before_data_updater():
    print("🦍 Waiting for bot to be ready before starting data updater...")
    await bot.wait_until_ready()

@auto_update_top.before_loop
async def before_auto_update():
    print("🦍 Waiting for bot to be ready before starting auto update...")
    await bot.wait_until_ready()

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "🦍 Ей, у тебе немає прав для цієї команди, хлопець!", 
            ephemeral=True
        )
    else:
        print(f"Command error: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "🦍 Ой-ой, щось пішло не так при виконанні команди!", 
                ephemeral=True
            )

async def main():
    token = os.getenv('TOKEN_BOT')
    if not token:
        print("ERROR: TOKEN_BOT не знайдено в змінних середовища")
        return
    
    print("Starting bot...")
    print(f"Bot token present: {bool(token)}")
    print(f"BM token present: {bool(os.getenv('TOKEN_BM'))}")
    
    try:
        print("Creating bot instance...")
        # Спочатку запускаємо бота без фонових задач
        await bot.start(token)
    except Exception as e:
        print(f"Failed to start bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
