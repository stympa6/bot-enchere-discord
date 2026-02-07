import os
import asyncio
import discord
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
    "ended": True
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
                "❌ L’enchère est terminée.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(BidModal())

# =======================
# MODAL DE MISE
# =======================
class BidModal(discord.ui.Modal, title="Placer une mise"):
    amount = discord.ui.TextInput(
        label="Montant de la mise (€)",
        placeholder="Ex: 150",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            bid_amount = int(self.amount.value)
        except ValueError:
            await interaction.response.send_message(
                "❌ Montant invalide.",
                ephemeral=True
            )
            return

        if bid_amount <= active_auction["highest_bid"]:
            await interaction.response.send_message(
                f"❌ La mise doit être supérieure à {active_auction['highest_bid']} €.",
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
            f"✅ Mise enregistrée : {bid_amount} €",
            ephemeral=True
        )

# =======================
# COMMANDE TEXTE POUR LANCER L’ENCHÈRE
# (PAS UNE SLASH COMMANDE)
# =======================
@bot.command()
@commands.has_permissions(administrator=True)
async def lancer(ctx, titre: str, prix_depart: int, duree: int):
    if not active_auction["ended"]:
        await ctx.send("❌ Une enchère est déjà en cours.")
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

    message = await ctx.send(embed=embed, view=BidView())

    active_auction.update({
        "message": message,
        "channel": ctx.channel,
        "highest_bid": prix_depart,
        "highest_bidder": None,
        "ended": False
    })

    await ctx.send(
        f"✅ Enchère lancée pour **{duree} minute(s)**"
    )

    await asyncio.sleep(duree * 60)

    active_auction["ended"] = True

    if active_auction["highest_bidder"]:
        await ctx.send(
            f"🏆 **Enchère terminée !**\n"
            f"Gagnant : {active_auction['highest_bidder'].mention}\n"
            f"Montant : **{active_auction['highest_bid']} €**"
        )
    else:
        await ctx.send("❌ Enchère terminée sans enchérisseur.")

# =======================
# READY : SUPPRESSION DES SLASH COMMANDS
# =======================
@bot.event
async def on_ready():
    try:
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print("🧹 Toutes les slash commands supprimées")
    except Exception as e:
        print("Erreur clear/sync :", e)

    print(f"✅ Bot connecté : {bot.user}")

bot.run(TOKEN)
