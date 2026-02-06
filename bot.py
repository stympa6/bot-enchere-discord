import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os

# =====================
# CONFIG
# =====================
GUILD_ID = 1468668056053219641
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# =====================
# VARIABLES ENCHÈRE
# =====================
enchere_active = False
vendeur = None
meilleure_offre = 0
meilleur_encherisseur = None
participants = set()

# =====================
# BOT READY
# =====================
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print("✅ Bot connecté")
    print("✅ Slash commands synchronisées (GUILD)")

# =====================
# COMMANDE /enchere
# =====================
@bot.tree.command(
    name="enchere",
    description="Lancer une enchère",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    prix_depart="Prix de départ",
    duree="Durée en secondes"
)
async def enchere(
    interaction: discord.Interaction,
    prix_depart: int,
    duree: int
):
    global enchere_active, vendeur, meilleure_offre, meilleur_encherisseur, participants

    if enchere_active:
        await interaction.response.send_message(
            "❌ Une enchère est déjà en cours",
            ephemeral=True
        )
        return

    enchere_active = True
    vendeur = interaction.user
    meilleure_offre = prix_depart
    meilleur_encherisseur = None
    participants = set()

    await interaction.response.send_message(
        f"🔥 **ENCHÈRE LANCÉE**\n"
        f"Vendeur : {vendeur.mention}\n"
        f"Prix de départ : **{prix_depart}€**\n"
        f"Durée : **{duree} secondes**\n\n"
        f"➡️ Utilisez `/miser` pour enchérir"
    )

    await asyncio.sleep(duree)

    enchere_active = False

    if meilleur_encherisseur:
        await interaction.channel.send(
            f"🏆 **ENCHÈRE TERMINÉE**\n"
            f"Gagnant : {meilleur_encherisseur.mention}\n"
            f"Prix final : **{meilleure_offre}€**\n\n"
            f"📩 {vendeur.mention} & {meilleur_encherisseur.mention}, contactez-vous !"
        )
    else:
        await interaction.channel.send(
            "❌ Enchère terminée sans aucune offre"
        )

# =====================
# COMMANDE /miser
# =====================
@bot.tree.command(
    name="miser",
    description="Faire une offre",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    montant="Montant de votre offre"
)
async def miser(interaction: discord.Interaction, montant: int):
    global meilleure_offre, meilleur_encherisseur, participants

    if not enchere_active:
        await interaction.response.send_message(
            "❌ Aucune enchère en cours",
            ephemeral=True
        )
        return

    if interaction.user == vendeur:
        await interaction.response.send_message(
            "❌ Le vendeur ne peut pas enchérir",
            ephemeral=True
        )
        return

    if montant <= meilleure_offre:
        await interaction.response.send_message(
            f"❌ L'offre doit être supérieure à {meilleure_offre}€",
            ephemeral=True
        )
        return

    meilleure_offre = montant
    meilleur_encherisseur = interaction.user
    participants.add(interaction.user)

    await interaction.response.send_message(
        f"💰 Nouvelle offre : **{montant}€** par {interaction.user.mention}"
    )

# =====================
# RUN
# =====================
bot.run(TOKEN)
