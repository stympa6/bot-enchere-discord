import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os

# ===== CONFIG =====
TOKEN = os.getenv("TOKEN")  # le token est dans les variables d’environnement
TICKET_CHANNEL_ID = 1468668834667040829  # salon où annoncer la fin

# ===== BOT =====
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== VIEW ENCHÈRE =====
class EnchereView(discord.ui.View):
    def __init__(self, vendeur, prix_depart, pas):
        super().__init__(timeout=None)
        self.vendeur = vendeur
        self.prix_actuel = prix_depart
        self.pas = pas
        self.meilleur_encherisseur = None

    @discord.ui.button(label="💰 Enchérir", style=discord.ButtonStyle.success)
    async def encherir(self, interaction: discord.Interaction, button: discord.ui.Button):

        # vendeur bloqué
        if interaction.user == self.vendeur:
            await interaction.response.send_message(
                "❌ Tu ne peux pas enchérir sur ta propre annonce",
                ephemeral=True
            )
            return

        # nouvelle enchère
        self.prix_actuel += self.pas
        self.meilleur_encherisseur = interaction.user

        await interaction.response.send_message(
            f"✅ Nouvelle enchère : **{self.prix_actuel}€** par {interaction.user.mention}",
            ephemeral=False
        )

    @discord.ui.button(label="ℹ️ Infos", style=discord.ButtonStyle.secondary)
    async def infos(self, interaction: discord.Interaction, button: discord.ui.Button):
        leader = (
            self.meilleur_encherisseur.mention
            if self.meilleur_encherisseur
            else "Aucun"
        )
        await interaction.response.send_message(
            f"💰 Prix actuel : **{self.prix_actuel}€**\n"
            f"🏆 Meilleur enchérisseur : {leader}",
            ephemeral=True
        )

# ===== EVENTS =====
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("✅ Bot prêt")

# ===== COMMANDE SLASH =====
@bot.tree.command(name="enchere_v2", description="Créer une enchère (v2)")
@app_commands.describe(
    prix="Prix de départ",
    duree="Durée en minutes",
    pas="Augmentation minimum (par défaut 10)"
)
async def enchere(
    interaction: discord.Interaction,
    prix: int,
    duree: int,
    pas: int = 10
):
    vendeur = interaction.user
    view = EnchereView(vendeur, prix, pas)

    embed = discord.Embed(
        title="🔥 Nouvelle enchère",
        description=(
            f"👤 **Vendeur** : {vendeur.mention}\n"
            f"💰 **Prix de départ** : {prix}€\n"
            f"⬆️ **Pas d’enchère** : {pas}€\n"
            f"⏱️ **Durée** : {duree} minute(s)"
        ),
        color=discord.Color.gold()
    )

    await interaction.response.send_message(embed=embed, view=view)

    # attente fin
    await asyncio.sleep(duree * 60)

    ticket_channel = bot.get_channel(TICKET_CHANNEL_ID)

    if ticket_channel:
        if view.meilleur_encherisseur:
            await ticket_channel.send(
                f"🏁 **ENCHÈRE TERMINÉE**\n"
                f"👤 Vendeur : {vendeur.mention}\n"
                f"🏆 Acheteur : {view.meilleur_encherisseur.mention}\n"
                f"💰 Prix final : **{view.prix_actuel}€**"
            )
        else:
            await ticket_channel.send(
                "⏰ Enchère terminée **sans aucune enchère**"
            )

# ===== RUN =====
if not TOKEN:
    raise ValueError("❌ TOKEN manquant (variable d’environnement)")

bot.run(TOKEN)
