import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("🧹 Nettoyage des slash commands...")
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync()
    print("✅ TOUTES les slash commands supprimées")
    await bot.close()

bot.run(TOKEN)
