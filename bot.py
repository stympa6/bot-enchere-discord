import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os

# ================== CONFIG ==================
TOKEN = os.getenv("TOKEN")  # NE JAMAIS mettre le token en dur
ANNONCE_CHANNEL_ID = 1468668834667040829  # salon annonces
# ============================================

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================== VIEW ==================
class EnchereView(discord.ui.View):
    def __init__(self, vendeur, prix_depart, duree_minutes, message):
        super().__init__(timeout=None)
        self.vendeur = vendeur
        self.prix = prix_depart
        self.meilleur_offrant = None
        self.message = message
        self.fin = False

    @discord.ui.button(label="💰 Miser +10€", style=discord.ButtonStyle.success)
    async def miser(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.fin:
            await interaction.response.send_message("⛔ Enchère terminée", ephemeral=True)
            return

        if interaction.user == self.vendeur:
            await interaction.response.send_message("❌ Tu ne peux pas miser sur ta propre enchère", ephemeral=True)
            return

        self.prix += 10
        self.meilleur_offrant = interaction.user

        embed = self.message.embeds[0]
        embed.set_field_at(
            1,
            name="💰 Meilleure offre",
            value=f"{self.prix}€ par {interaction.user.mention}",
            inline=False
        )

        await self.message.edit(embed=embed, view=self)
        await interaction.response.send_message("✅ Mise enregistrée", ephemeral=True)

# ================== EVENTS ==================
@bot.event
async def on_ready():
    # 🔥 FORÇAGE DU CACHE DISCORD
    await bot.tree.clear_commands(guild=None)
    await bot.tree.sync()
    print("✅ Commandes slash resynchronisées")

# ================== COMMAND ==================
@bot.tree.command(name="enchere", description="Créer une enchère")
@app_commands.describe(
    prix="Prix de départ",
    duree="Durée de l'enchère EN MINUTES"
)
async def enchere(interaction: discord.Interaction, prix: int, duree: int):

    vendeur = interaction.user
    channel = interaction.channel

    embed = discord.Embed(
        title="🔥 Nouvelle enchère",
        color=discord.Color.gold()
    )
    embed.add_field(name="👤 Vendeur", value=vendeur.mention, inline=False)
    embed.add_field(name="💰 Meilleure offre", value=f"{prix}€", inline=False)
    embed.add_field(name="⏱️ Durée", value=f"{duree} minutes", inline=False)

    message = await channel.send(embed=embed)
    view = EnchereView(vendeur, prix, duree, message)
    await message.edit(view=view)

    await interaction.response.send_message("✅ Enchère lancée", ephemeral=True)

    # ⏳ attente EN MINUTES
    await asyncio.sleep(duree * 60)

    view.fin = True

    if view.meilleur_offrant:
        await channel.send(
            f"🎉 **Enchère terminée !**\n"
            f"👤 Vendeur : {vendeur.mention}\n"
            f"🏆 Acheteur : {view.meilleur_offrant.mention}\n"
            f"💰 Prix final : {view.prix}€"
        )
    else:
        await channel.send("⏰ Enchère terminée sans aucune mise")

    # ❌ suppression du message d'enchère
    await message.delete()

# ================== RUN ==================
if not TOKEN:
    raise ValueError("TOKEN manquant (variable d’environnement)")

bot.run(TOKEN)
