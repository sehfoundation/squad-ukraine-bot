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
        try:
            # Очікуємо готовності бота
            await self.wait_until_ready()
            
            # Синхронізуємо команди
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} slash commands")
            
            # Виводимо список команд для діагностики
            for command in synced:
                print(f"  - {command.name}: {command.description}")
                
        except Exception as e:
            print(f"Failed to sync commands: {e}")
        
        # Запускаємо фонові задачі після синхронізації
        if not self.data_updater.is_running():
            self.data_updater.start()
        if not self.auto_update_top.is_running():
            self.auto_update_top.start()
        
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guilds')
        
        # Ініціалізуємо дані при старті
        await data_cache.update_data()

bot = SquadBot()

def is_allowed_user():
    """Декоратор для перевірки дозволених користувачів"""
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id in Settings.ALLOWED_USER_IDS
    return app_commands.check(predicate)

def is_admin_user():
    """Декоратор для перевірки адмін користувачів"""
    def predicate(interaction: discord.Interaction) -> bool:
        # Перевіряємо чи користувач в списку дозволених та є адміністратором сервера
        if interaction.user.id not in Settings.ALLOWED_USER_IDS:
            return False
        
        if not interaction.guild:
            return True  # Якщо немає гільдії, дозволяємо
            
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return True
            
        return (
            member.guild_permissions.administrator or
            member.guild_permissions.manage_guild or
            interaction.guild.owner_id == interaction.user.id
        )
    return app_commands.check(predicate)

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
        
        # Надсилаємо перший embed (публічно)
        await interaction.edit_original_response(content=None, embed=embeds[0])
        
        # Надсилаємо інші embed'и як followup повідомлення (також публічно)
        for embed in embeds[1:]:
            await interaction.followup.send(embed=embed, ephemeral=False)
            
    except Exception as e:
        print(f"Error in top command: {e}")
        await interaction.edit_original_response(content="🦍 Ой, щось зламалось при отриманні даних. Спробуй ще раз!")

@bot.tree.command(name="topad", description="Топ 100 онлайн за поточний місяць (Steam ID + нік + час) - тільки для адмінів")
@is_admin_user()
async def top_admin_command(interaction: discord.Interaction):
    await interaction.response.send_message("🦍 Завантажую секретні дані з кешу, це тільки для крутих...", ephemeral=True)
    
    try:
        players_list = data_cache.get_current_month_data(with_steam_id=True)
        
        if not players_list:
            status = data_cache.get_cache_status()
            await interaction.edit_original_response(content=f"🦍 Оу, немає даних в кеші, мабуть щось зламалось.\n{status}")
            return
        
        embeds = create_leaderboard_embeds(players_list, is_admin=True, title_suffix="")
        
        # Надсилаємо перший embed
        await interaction.edit_original_response(content=None, embed=embeds[0])
        
        # Надсилаємо інші embed'и як followup повідомлення
        for embed in embeds[1:]:
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    except Exception as e:
        print(f"Error in topad command: {e}")
        await interaction.edit_original_response(content="🦍 Йой, щось пішло не так з данними. Попробуй ще раз пізніше!")

@bot.tree.command(name="toppr", description="Топ 100 онлайн за попередній місяць (Steam ID + нік + час) - тільки для адмінів")
@is_admin_user()
async def top_previous_month_command(interaction: discord.Interaction):
    await interaction.response.send_message("🦍 Шукаю дані старого місяця в кеші, це займе трошки часу...", ephemeral=True)
    
    try:
        players_list = data_cache.get_previous_month_data()
        
        if not players_list:
            status = data_cache.get_cache_status()
            await interaction.edit_original_response(content=f"🦍 Хм, немає даних минулого місяця в кеші, щось не грає.\n{status}")
            return
        
        embeds = create_leaderboard_embeds(players_list, is_admin=True, title_suffix=" (попередній місяць)")
        
        # Надсилаємо перший embed
        await interaction.edit_original_response(content=None, embed=embeds[0])
        
        # Надсилаємо інші embed'и як followup повідомлення
        for embed in embeds[1:]:
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    except Exception as e:
        print(f"Error in toppr command: {e}")
        await interaction.edit_original_response(content="🦍 Аяяй, щось не так з данними минулого місяця. Спробуй пізніше!")

@bot.tree.command(name="randomsquadname", description="Генерує випадкову назву для Squad загону")
@is_allowed_user()
async def random_squad_name_command(interaction: discord.Interaction):
    # Список прикметників (50 слів)
    adjectives = [
        "Човгаючі", "Чорні", "Коренасті", "Сонливі", "Крихкі", "Середні", "Грайливі",
        "Великі", "Білі", "Швидкі", "Повільні", "Хитрі", "Качьові", "Боязкі",
        "Старі", "Молоді", "Досвідчені", "Імператорські", "Тихі", "Гучні",
        "Терпеливі", "Нетерпеливі", "Гадячські", "Дурні", "Веселі", "Сумні",
        "Злі", "Гачі", "Холодні", "Гарячі", "Мокрі", "Сухі",
        "Голодні", "Ситі", "Втомлені", "Гачі", "Спокійні", "Нервові",
        "Секретні", "Сластиві", "Таємничі", "Очевидні", "Складні", "Прості",
        "Орущі", "Домашні", "Вільні", "Заплутані", "Райдужні", "Випадкові", "Українські", "Вмотивовані", "Заземлені", "Некурящі", "Сомалійські"
    ]
    
    # Список іменників у множині (50 слів)
    nouns = [
        "десантники", "карлики", "алконавти", "космодесантники", "депутати", "члени",
        "солдати", "шиншили", "льотчики", "снайпери", "тактикульщики", "вісти",
        "розвідники", "командири", "рядові", "сержанти", "офіцери", "генерали",
        "піхотинці", "артилеристи", "зв'язківці", "водії", "механіки", "кулеметники",
        "сомалійці", "плитовкладачі", "диверсанти", "штурмовики", "гачімени", "нападники",
        "бойовики", "новобранці", "добровольці", "контрактники", "призовники", "резервісти",
        "дюшеси", "крокодили", "цицькодави", "легіонери", "гвардійці", "рейнджери",
        "шоколодки чайка", "сироїди", "миротворці", "патрульні", "собачатники", "полтавці",
        "гренадери", "кавалеристи", "махновці", "зрадойби", "фани телемарафону"
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
@is_admin_user()
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
@is_admin_user()
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

def create_leaderboard_embeds(players_list, is_admin: bool = False, title_suffix: str = ""):
    """Створює embed'и для лідерборду"""
    embeds = []
    players_per_page = 50
    
    for i in range(0, len(players_list), players_per_page):
        page_players = players_list[i:i + players_per_page]
        page_message = ""
        
        for j, player in enumerate(page_players):
            position = i + j + 1
            if is_admin:
                line = f"{position}. **{player.steam_id}** **{player.name}**: {Tools.format_time(player.value)}"
            else:
                line = f"{position}. **{player.name}**: {Tools.format_time(player.value)}"
            
            page_message += line + "\n"
        
        page_num = (i // players_per_page) + 1
        total_pages = (len(players_list) + players_per_page - 1) // players_per_page
        
        embed = discord.Embed(
            title=f"Top 100 Online — SQUAD UKRAINE{title_suffix} (сторінка {page_num}/{total_pages})",
            description=page_message,
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        if data_cache.last_update:
            embed.set_footer(text=f"🦍 Оновлено: {data_cache.last_update.strftime('%H:%M:%S UTC')}")
        
        embeds.append(embed)
    
    return embeds

@tasks.loop(seconds=Settings.DATA_UPDATE_INTERVAL)
async def data_updater():
    """Фонова задача для оновлення даних кожні 10 хвилин"""
    print("🦍 Starting scheduled data update...")
    await data_cache.update_data()

@tasks.loop(minutes=10)
async def auto_update_top():
    """Фонова задача для автоматичного оновлення топу"""
    if not Settings.AUTO_UPDATE_CHANNEL_ID or not bot.auto_update_message_id:
        return
    
    try:
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
    await bot.wait_until_ready()

@auto_update_top.before_loop
async def before_auto_update():
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
    try:
        await bot.start(token)
    except Exception as e:
        print(f"Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
