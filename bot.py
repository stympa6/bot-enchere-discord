import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("🧹 SUPPRESSION TOTALE DES SLASH COMMANDS...")
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync()
    print("✅ TOUTES LES COMMANDES SONT SUPPRIMÉES")
    await bot.close()

bot.run(TOKEN)
