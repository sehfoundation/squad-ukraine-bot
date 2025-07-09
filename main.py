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
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
    async def setup_hook(self):
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")
        
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')

bot = SquadBot()

@bot.tree.command(name="top", description="Топ 100 онлайн за поточний місяць (нік + час)")
async def top_command(interaction: discord.Interaction):
    await handle_top_command(interaction, is_current_month=True, is_admin=False)

@bot.tree.command(name="topad", description="Топ 100 онлайн за поточний місяць (нік + час + SteamID)")
async def top_admin_command(interaction: discord.Interaction):
    await handle_top_command(interaction, is_current_month=True, is_admin=True)

@bot.tree.command(name="toppr", description="Топ 100 онлайн за попередній місяць (нік + час + SteamID)")
async def top_previous_month_command(interaction: discord.Interaction):
    await handle_top_command(interaction, is_current_month=False, is_admin=True)

async def handle_top_command(interaction: discord.Interaction, is_current_month: bool, is_admin: bool):
    await interaction.response.defer()
    
    try:
        parser = Parser()
        players_list = await parser.fetch_and_parse_leaderboard(is_admin, is_current_month)
        
        leaderboard_message = ""
        for i, player in enumerate(players_list):
            line = f"{i + 1}. **{player.name}**: {Tools.format_time(player.value)}"
            if is_admin:
                line += f" — {player.steam_id}"
            leaderboard_message += line + "\n"
        
        embed = discord.Embed(
            title="Top 100 Online — SQUAD UKRAINE",
            description=leaderboard_message,
            color=discord.Color.blue()
        )
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"Error in top command: {e}")
        await interaction.followup.send("Виникла помилка при отриманні даних. Спробуйте пізніше.")

async def main():
    token = os.getenv('TOKEN_BOT')
    if not token:
        raise ValueError("TOKEN_BOT не знайдено в змінних середовища")
    
    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
