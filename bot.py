import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# =======================
# STOCKAGE ENCHÈRE
# =======================
active_auction = {
    "message": None,
    "channel": None,
    "highest_bid": 0,
    "highest_bidder": None,
    "ended": False
}

# =======================
# BOUTON MISER
# =======================
class BidView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💰 Miser", style=discord.ButtonStyle.green)
    async def bid(self, interaction: discord.Interaction, button: discord.ui.Button):
        if active_auction["ended"]:
            await interaction.response.send_message(
                "❌ L’enchère est terminée.", ephemeral=True
            )
            return

        modal = BidModal()
        await interaction.response.send_modal(modal)

# =======================
# MODAL POUR MISER
# =======================
class BidModal(discord.ui.Modal, title="Placer une mise"):
    amount = discord.ui.TextInput(
        label="Montant de la mise",
        placeholder="Ex: 150",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            bid_amount = int(self.amount.value)
        except ValueError:
            await interaction.response.send_message(
                "❌ Montant invalide.", ephemeral=True
            )
            return

        if bid_amount <= active_auction["highest_bid"]:
            await interaction.response.send_message(
                f"❌ La mise doit être supérieure à {active_auction['highest_bid']}.",
                ephemeral=True
            )
            return

        active_auction["highest_bid"] = bid_amount
        active_auction["highest_bidder"] = interaction.user

        embed = active_auction["message"].embeds[0]
        embed.set_field_at(
            0,
            name="💸 Enchère actuelle",
            value=f"{bid_amount} € par {interaction.user.mention}",
            inline=False
        )

        await active_auction["message"].edit(embed=embed, view=BidView())
        await interaction.response.send_message(
            f"✅ Mise acceptée : {bid_amount} €", ephemeral=True
        )

# =======================
# COMMANDE /ENCHERE
# =======================
@bot.tree.command(name="enchere", description="Lancer une enchère")
@app_commands.describe(
    titre="Titre de l’enchère",
    prix_depart="Prix de départ",
    duree="Durée en minutes"
)
async def enchere(
    interaction: discord.Interaction,
    titre: str,
    prix_depart: int,
    duree: int
):
    if active_auction["message"] and not active_auction["ended"]:
        await interaction.response.send_message(
            "❌ Une enchère est déjà en cours.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=f"🧾 Enchère : {titre}",
        description="Clique sur **Miser** pour participer",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="💸 Enchère actuelle",
        value=f"{prix_depart} € (aucun enchérisseur)",
        inline=False
    )

    message = await interaction.channel.send(
        embed=embed,
        view=BidView()
    )

    active_auction.update({
        "message": message,
        "channel": interaction.channel,
        "highest_bid": prix_depart,
        "highest_bidder": None,
        "ended": False
    })

    await interaction.response.send_message(
        f"✅ Enchère lancée pour **{duree} minute(s)**",
        ephemeral=True
    )

    # ⏱️ FIN DE L’ENCHÈRE
    await asyncio.sleep(duree * 60)

    active_auction["ended"] = True

    if active_auction["highest_bidder"]:
        await interaction.channel.send(
            f"🏆 **Enchère terminée !**\n"
            f"Gagnant : {active_auction['highest_bidder'].mention}\n"
            f"Montant : **{active_auction['highest_bid']} €**"
        )
    else:
        await interaction.channel.send(
            "❌ Enchère terminée sans enchérisseur."
        )

# =======================
# READY + RESYNC PROPRE
# =======================
@bot.event
async def on_ready():
    try:
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print("✅ Bot prêt – commandes synchronisées")
    except Exception as e:
        print("❌ Erreur sync :", e)

bot.run(TOKEN)
