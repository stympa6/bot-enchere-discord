import discord
from discord.ext import commands
import asyncio

# =======================
# ⚠️ METS TON TOKEN ICI
# =======================
import os
TOKEN = os.getenv("DISCORD_TOKEN")

# =======================
# INTENTS
# =======================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

print("🔥 BOT.PY LANCÉ 🔥")

# =======================
# STOCKAGE ENCHÈRE
# =======================
active_auction = {
    "message": None,
    "channel": None,
    "title": "",
    "image": None,
    "highest_bid": 0,
    "highest_bidder": None,
    "ended": True,
    "remaining": 0
}

# =======================
# EMBED CENTRAL
# =======================
def build_embed():
    bidder = (
        active_auction["highest_bidder"].mention
        if active_auction["highest_bidder"]
        else "Aucun"
    )

    minutes = active_auction["remaining"] // 60
    seconds = active_auction["remaining"] % 60

    embed = discord.Embed(
        title=f"🧾 ENCHÈRE — {active_auction['title']}",
        description="💰 Clique sur **MISER** pour participer",
        color=discord.Color.gold() if not active_auction["ended"] else discord.Color.red()
    )

    embed.add_field(
        name="💰 Meilleure offre",
        value=f"**{active_auction['highest_bid']} €**\n👤 {bidder}",
        inline=True
    )

    embed.add_field(
        name="⏳ Temps restant",
        value=f"{minutes:02d}:{seconds:02d}",
        inline=True
    )

    if active_auction["image"]:
        embed.set_image(url=active_auction["image"])

    embed.set_footer(
        text="⛔ Enchère terminée" if active_auction["ended"] else "⏱️ Enchère en cours"
    )

    return embed

# =======================
# VIEW + BOUTON
# =======================
class BidView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💰 MISER", style=discord.ButtonStyle.success)
    async def bid(self, interaction: discord.Interaction, button: discord.ui.Button):
        if active_auction["ended"]:
            await interaction.response.send_message(
                "❌ Enchère terminée.", ephemeral=True
            )
            return

        await interaction.response.send_modal(BidModal())

# =======================
# MODAL
# =======================
class BidModal(discord.ui.Modal, title="💰 Placer une mise"):
    amount = discord.ui.TextInput(
        label="Montant (€)",
        placeholder="Ex: 50",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            bid_amount = int(self.amount.value)
        except ValueError:
            await interaction.response.send_message("❌ Nombre invalide.", ephemeral=True)
            return

        current = active_auction["highest_bid"]

        if bid_amount > current + 10:
            await interaction.response.send_message(
                f"❌ Augmentation max **+10€** (max : {current + 10}€)",
                ephemeral=True
            )
            return

        if bid_amount <= current:
            await interaction.response.send_message(
                f"❌ Mise trop basse (actuelle : {current}€)",
                ephemeral=True
            )
            return

        active_auction["highest_bid"] = bid_amount
        active_auction["highest_bidder"] = interaction.user

        await active_auction["message"].edit(
            embed=build_embed(),
            view=BidView()
        )

        await interaction.response.send_message(
            f"✅ Mise acceptée : **{bid_amount}€**",
            ephemeral=True
        )

# =======================
# !START (IMAGE JOINTE)
# =======================
@bot.command(name="start")
async def start(ctx, titre: str, prix_depart: int, duree: int):
    if not active_auction["ended"]:
        await ctx.send("❌ Une enchère est déjà en cours.")
        return

    image_url = None
    if ctx.message.attachments:
        image_url = ctx.message.attachments[0].url

    active_auction.update({
        "message": None,
        "channel": ctx.channel,
        "title": titre,
        "image": image_url,
        "highest_bid": prix_depart,
        "highest_bidder": None,
        "ended": False,
        "remaining": duree * 60
    })

    message = await ctx.send(
        embed=build_embed(),
        view=BidView()
    )

    active_auction["message"] = message

    while active_auction["remaining"] > 0 and not active_auction["ended"]:
        await asyncio.sleep(1)
        active_auction["remaining"] -= 1
        await message.edit(embed=build_embed())

    if active_auction["ended"]:
        return

    active_auction["ended"] = True
    await message.edit(embed=build_embed(), view=None)

    if active_auction["highest_bidder"]:
        await ctx.send(
            f"🏆 **ENCHÈRE TERMINÉE !**\n"
            f"Gagnant : {active_auction['highest_bidder'].mention}\n"
            f"Montant : **{active_auction['highest_bid']}€**"
        )
    else:
        await ctx.send("❌ Enchère terminée sans enchérisseur.")

# =======================
# !CANCEL
# =======================
@bot.command(name="cancel")
async def cancel(ctx):
    if active_auction["ended"]:
        await ctx.send("❌ Aucune enchère en cours.")
        return

    active_auction["ended"] = True
    await active_auction["message"].edit(embed=build_embed(), view=None)
    await ctx.send("🛑 Enchère annulée.")

# =======================
# READY
# =======================
@bot.event
async def on_ready():
    print(f"✅ Bot connecté : {bot.user}")

bot.run(TOKEN)
