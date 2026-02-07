import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# STOCKAGE ENCHÈRE
# =========================
auction = {
    "active": False,
    "seller": None,
    "item": None,
    "price": 0,
    "highest_bidder": None,
    "message": None
}

# =========================
# READY + RESYNC
# =========================
@bot.event
async def on_ready():
    try:
        bot.tree.clear_commands()
        await bot.tree.sync()
    except:
        pass

    print("✅ Bot prêt – commandes synchronisées")

# =========================
# BOUTON MISER
# =========================
class BidView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💰 Miser", style=discord.ButtonStyle.green)
    async def bid(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not auction["active"]:
            await interaction.response.send_message("❌ L’enchère est terminée.", ephemeral=True)
            return

        if interaction.user.id == auction["seller"]:
            await interaction.response.send_message("❌ Le vendeur ne peut pas miser.", ephemeral=True)
            return

        new_price = auction["price"] + 1
        auction["price"] = new_price
        auction["highest_bidder"] = interaction.user.id

        embed = auction["message"].embeds[0]
        embed.set_field_at(
            1,
            name="💸 Offre actuelle",
            value=f"{auction['price']} €",
            inline=False
        )
        embed.set_field_at(
            2,
            name="🏆 Meilleur enchérisseur",
            value=f"<@{interaction.user.id}>",
            inline=False
        )

        await auction["message"].edit(embed=embed, view=self)
        await interaction.response.send_message(f"✅ Mise acceptée : **{new_price} €**", ephemeral=True)

# =========================
# COMMANDE /ENCHERE
# =========================
@bot.tree.command(name="enchere", description="Lancer une enchère")
@app_commands.describe(
    objet="Objet à vendre",
    prix_depart="Prix de départ",
    duree="Durée en minutes"
)
async def enchere(
    interaction: discord.Interaction,
    objet: str,
    prix_depart: int,
    duree: int
):

    if auction["active"]:
        await interaction.response.send_message("❌ Une enchère est déjà en cours.", ephemeral=True)
        return

    auction["active"] = True
    auction["seller"] = interaction.user.id
    auction["item"] = objet
    auction["price"] = prix_depart
    auction["highest_bidder"] = None

    embed = discord.Embed(
        title="🔥 ENCHÈRE EN COURS",
        color=discord.Color.gold()
    )
    embed.add_field(name="📦 Objet", value=objet, inline=False)
    embed.add_field(name="💸 Offre actuelle", value=f"{prix_depart} €", inline=False)
    embed.add_field(name="🏆 Meilleur enchérisseur", value="Aucun", inline=False)
    embed.set_footer(text=f"⏱️ Durée : {duree} minute(s)")

    await interaction.response.send_message(embed=embed, view=BidView())
    msg = await interaction.original_response()
    auction["message"] = msg

    await asyncio.sleep(duree * 60)

    # =========================
    # FIN ENCHÈRE
    # =========================
    auction["active"] = False

    if auction["highest_bidder"]:
        await interaction.channel.send(
            f"🏁 **Enchère terminée !**\n"
            f"📦 **{auction['item']}**\n"
            f"🏆 Gagnant : <@{auction['highest_bidder']}>\n"
            f"💰 Prix final : **{auction['price']} €**\n"
            f"👤 Vendeur : <@{auction['seller']}>"
        )
    else:
        await interaction.channel.send("❌ Enchère terminée sans aucune offre.")

# =========================
# RUN
# =========================
if TOKEN is None:
    raise RuntimeError("❌ TOKEN manquant (variable d’environnement)")

bot.run(TOKEN)
