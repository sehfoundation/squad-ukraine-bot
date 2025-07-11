import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from dotenv import load_dotenv
from parser import Parser
from tools import Tools

load_dotenv()

class SquadBot(commands.Bot):
    def __init__(self):
        # Використовуємо найпростіші intents + права для перевірки серверів
        intents = discord.Intents.none()
        intents.guilds = True  # Потрібно для slash команд та перевірки прав
        super().__init__(command_prefix='!', intents=intents)
        
    async def setup_hook(self):
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} slash commands")
        except Exception as e:
            print(f"Failed to sync commands: {e}")
        
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guilds')

bot = SquadBot()

@bot.tree.command(name="top", description="Топ 100 онлайн за поточний місяць (нік + час)")
async def top_command(interaction: discord.Interaction):
    await handle_top_command(interaction, is_current_month=True, is_admin=False)

@bot.tree.command(name="topad", description="Топ 100 онлайн за поточний місяць (нік + час + SteamID) - тільки для адмінів")
async def top_admin_command(interaction: discord.Interaction):
    # Відповідаємо спочатку, потім перевіряємо права
    await interaction.response.send_message("🔄 Перевіряю права доступу...", ephemeral=True)
    
    try:
        # Діагностика - логуємо інформацію
        print(f"Guild: {interaction.guild}")
        print(f"Guild ID: {interaction.guild_id if interaction.guild else 'None'}")
        print(f"User: {interaction.user}")
        print(f"User ID: {interaction.user.id}")
        
        # Якщо гільдія недоступна, спробуємо отримати через bot
        guild = interaction.guild
        if not guild and interaction.guild_id:
            guild = bot.get_guild(interaction.guild_id)
            print(f"Got guild from bot: {guild}")
        
        if not guild:
            # Пропускаємо перевірку прав і йдемо далі
            print("No guild found, skipping permission check")
            await interaction.edit_original_response(content="🔄 Завантажую дані...")
            await handle_top_command_admin(interaction, is_current_month=True, is_admin=True)
            return
        
        # Отримуємо член сервера
        member = guild.get_member(interaction.user.id)
        print(f"Member: {member}")
        
        if not member:
            # Спробуємо отримати через fetch
            try:
                member = await guild.fetch_member(interaction.user.id)
                print(f"Fetched member: {member}")
            except:
                print("Could not fetch member, skipping permission check")
                await interaction.edit_original_response(content="🔄 Завантажую дані...")
                await handle_top_command_admin(interaction, is_current_month=True, is_admin=True)
                return
        
        # Перевіряємо різні види прав
        is_admin = (
            member.guild_permissions.administrator or  # Права адміністратора
            member.guild_permissions.manage_guild or   # Права керування сервером
            member.guild_permissions.manage_channels or # Права керування каналами
            guild.owner_id == interaction.user.id  # Власник сервера
        )
        
        print(f"Admin permissions: admin={member.guild_permissions.administrator}, "
              f"manage_guild={member.guild_permissions.manage_guild}, "
              f"manage_channels={member.guild_permissions.manage_channels}, "
              f"is_owner={guild.owner_id == interaction.user.id}")
        
        if not is_admin:
            await interaction.edit_original_response(content="❌ Ця команда доступна тільки адміністраторам сервера.")
            return
        
        # Оновлюємо повідомлення та продовжуємо
        await interaction.edit_original_response(content="🔄 Завантажую дані...")
        await handle_top_command_admin(interaction, is_current_month=True, is_admin=True)
    except Exception as e:
        print(f"Error in topad command: {e}")
        # У разі помилки просто виконуємо команду без перевірки прав
        await interaction.edit_original_response(content="🔄 Завантажую дані...")
        await handle_top_command_admin(interaction, is_current_month=True, is_admin=True)

@bot.tree.command(name="toppr", description="Топ 100 онлайн за попередній місяць (нік + час + SteamID) - тільки для адмінів")
async def top_previous_month_command(interaction: discord.Interaction):
    # Відповідаємо спочатку, потім перевіряємо права
    await interaction.response.send_message("🔄 Перевіряю права доступу...", ephemeral=True)
    
    try:
        # Якщо гільдія недоступна, спробуємо отримати через bot
        guild = interaction.guild
        if not guild and interaction.guild_id:
            guild = bot.get_guild(interaction.guild_id)
        
        if not guild:
            # Пропускаємо перевірку прав і йдемо далі
            await interaction.edit_original_response(content="🔄 Завантажую дані...")
            await handle_top_command_admin(interaction, is_current_month=False, is_admin=True)
            return
        
        # Отримуємо член сервера
        member = guild.get_member(interaction.user.id)
        
        if not member:
            # Спробуємо отримати через fetch
            try:
                member = await guild.fetch_member(interaction.user.id)
            except:
                await interaction.edit_original_response(content="🔄 Завантажую дані...")
                await handle_top_command_admin(interaction, is_current_month=False, is_admin=True)
                return
        
        # Перевіряємо різні види прав
        is_admin = (
            member.guild_permissions.administrator or  # Права адміністратора
            member.guild_permissions.manage_guild or   # Права керування сервером
            member.guild_permissions.manage_channels or # Права керування каналами
            guild.owner_id == interaction.user.id  # Власник сервера
        )
        
        if not is_admin:
            await interaction.edit_original_response(content="❌ Ця команда доступна тільки адміністраторам сервера.")
            return
        
        # Оновлюємо повідомлення та продовжуємо
        await interaction.edit_original_response(content="🔄 Завантажую дані...")
        await handle_top_command_admin(interaction, is_current_month=False, is_admin=True)
    except Exception as e:
        print(f"Error in toppr command: {e}")
        # У разі помилки просто виконуємо команду без перевірки прав
        await interaction.edit_original_response(content="🔄 Завантажую дані...")
        await handle_top_command_admin(interaction, is_current_month=False, is_admin=True)

async def handle_top_command_admin(interaction: discord.Interaction, is_current_month: bool, is_admin: bool):
    try:
        parser = Parser()
        players_list = await parser.fetch_and_parse_leaderboard(is_admin, is_current_month)
        
        if not players_list:
            await interaction.edit_original_response(content="❌ Не вдалося отримати дані. Спробуйте пізніше.")
            return
        
        # Розділяємо на частини для уникнення ліміту Discord
        embeds = []
        current_message = ""
        players_per_page = 50  # Показуємо по 50 гравців на сторінку
        
        for i in range(0, len(players_list), players_per_page):
            page_players = players_list[i:i + players_per_page]
            page_message = ""
            
            for j, player in enumerate(page_players):
                position = i + j + 1
                if is_admin:
                    # Формат для адмінів: "1. 76561198123456789 PlayerName: 1d 2h 3m 4s"
                    line = f"{position}. **{player.steam_id}** **{player.name}**: {Tools.format_time(player.value)}"
                else:
                    # Формат для звичайних користувачів: "1. PlayerName: 1d 2h 3m 4s"
                    line = f"{position}. **{player.name}**: {Tools.format_time(player.value)}"
                
                page_message += line + "\n"
            
            page_num = (i // players_per_page) + 1
            total_pages = (len(players_list) + players_per_page - 1) // players_per_page
            
            embed = discord.Embed(
                title=f"Top 100 Online — SQUAD UKRAINE (сторінка {page_num}/{total_pages})",
                description=page_message,
                color=discord.Color.blue()
            )
            embeds.append(embed)
        
        # Надсилаємо перший embed
        await interaction.edit_original_response(content=None, embed=embeds[0])
        
        # Надсилаємо інші embed'и як followup повідомлення
        for embed in embeds[1:]:
            await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        print(f"Error in admin top command: {e}")
        await interaction.edit_original_response(content="❌ Виникла помилка при отриманні даних. Спробуйте пізніше.")

async def handle_top_command(interaction: discord.Interaction, is_current_month: bool, is_admin: bool):
    # Відповідаємо відразу, що починаємо обробку
    await interaction.response.send_message("🔄 Завантажую дані...", ephemeral=True)
    
    try:
        parser = Parser()
        players_list = await parser.fetch_and_parse_leaderboard(is_admin, is_current_month)
        
        if not players_list:
            await interaction.edit_original_response(content="❌ Не вдалося отримати дані. Спробуйте пізніше.")
            return
        
        # Розділяємо на частини для уникнення ліміту Discord
        embeds = []
        current_message = ""
        players_per_page = 50  # Показуємо по 50 гравців на сторінку
        
        for i in range(0, len(players_list), players_per_page):
            page_players = players_list[i:i + players_per_page]
            page_message = ""
            
            for j, player in enumerate(page_players):
                position = i + j + 1
                if is_admin:
                    # Формат для адмінів: "1. 76561198123456789 PlayerName: 1d 2h 3m 4s"
                    line = f"{position}. **{player.steam_id}** **{player.name}**: {Tools.format_time(player.value)}"
                else:
                    # Формат для звичайних користувачів: "1. PlayerName: 1d 2h 3m 4s"
                    line = f"{position}. **{player.name}**: {Tools.format_time(player.value)}"
                
                page_message += line + "\n"
            
            page_num = (i // players_per_page) + 1
            total_pages = (len(players_list) + players_per_page - 1) // players_per_page
            
            embed = discord.Embed(
                title=f"Top 100 Online — SQUAD UKRAINE (сторінка {page_num}/{total_pages})",
                description=page_message,
                color=discord.Color.blue()
            )
            embeds.append(embed)
        
        # Надсилаємо перший embed
        await interaction.edit_original_response(content=None, embed=embeds[0])
        
        # Надсилаємо інші embed'и як followup повідомлення
        for embed in embeds[1:]:
            await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        print(f"Error in top command: {e}")
        await interaction.edit_original_response(content="❌ Виникла помилка при отриманні даних. Спробуйте пізніше.")

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
