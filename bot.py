import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os

TOKEN = os.getenv("TOKEN")

TICKET_CHANNEL_ID = 1468668834667040829

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- VIEW ENCHERE ----------
class EnchereView(discord.ui.View):
    def __init__(self, vendeur, prix):
        super().__init__(timeout=None)
        self.vendeur = vendeur
        self.prix_actuel = prix
        self.meilleur_encherisseur = None

    @discord.ui.button(label="💰 Miser +10€", style=discord.ButtonStyle.success)
    async def miser(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.vendeur:
            await interaction.response.send_message(
                "❌ Tu ne peux pas miser sur ta propre enchère.",
                ephemeral=True
            )
            return

        self.prix_actuel += 10
        self.meilleur_encherisseur = interaction.user

        await interaction.message.edit(
            embed=discord.Embed(
                title="🔥 Enchère en cours",
                description=(
                    f"👤 Vendeur : {self.vendeur.mention}\n"
                    f"💰 Offre actuelle : **{self.prix_actuel}€**\n"
                    f"🏆 Meilleur enchérisseur : {interaction.user.mention}"
                ),
                color=discord.Color.gold()
            ),
            view=self
        )

        await interaction.response.defer()

# ---------- BOT READY ----------
@bot.event
async def on_ready():
    try:
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print("🧹 Anciennes commandes supprimées")
    except:
        pass

    await bot.tree.sync()
    print("✅ Bot prêt avec commandes slash (V2)")

# ---------- COMMANDE SLASH V2 ----------
@bot.tree.command(
    name="enchere_v2",
    description="Créer une enchère avec système de mise"
)
@app_commands.describe(prix="Prix de départ", duree="Durée en minutes")
async def enchere_v2(interaction: discord.Interaction, prix: int, duree: int):
    vendeur = interaction.user
    view = EnchereView(vendeur, prix)

    embed = discord.Embed(
        title="🔥 Nouvelle enchère (V2)",
        description=(
            f"👤 Vendeur : {vendeur.mention}\n"
            f"💰 Offre actuelle : **{prix}€**\n"
            f"⏱️ Durée : **{duree} minutes**"
        ),
        color=discord.Color.gold()
    )

    await interaction.response.send_message(embed=embed, view=view)

    await asyncio.sleep(duree * 60)

    if view.meilleur_encherisseur:
        channel = interaction.channel
        await channel.send(
            f"🎉 **Enchère terminée**\n"
            f"👤 Vendeur : {vendeur.mention}\n"
            f"🏆 Gagnant : {view.meilleur_encherisseur.mention}\n"
            f"💰 Prix final : {view.prix_actuel}€"
        )
    else:
        await interaction.channel.send("⏰ Enchère terminée sans enchérisseur.")

bot.run(TOKEN)
