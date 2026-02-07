import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- CONFIG ----------------
ANNONCE_CHANNEL_ID = 1468668834667040829  # salon annonces
TICKET_CATEGORY_ID = 1468669605353361520  # catégorie tickets
MISE_INCREMENT = 10
# ---------------------------------------

auction = {
    "active": False,
    "price": 0,
    "winner": None,
    "message": None,
    "task": None
}

# ---------- BOUTON MISER ----------
class BidButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💰 Miser +10€", style=discord.ButtonStyle.green)
    async def bid(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not auction["active"]:
            await interaction.response.send_message("❌ L'enchère est terminée.", ephemeral=True)
            return

        auction["price"] += MISE_INCREMENT
        auction["winner"] = interaction.user

        embed = auction["message"].embeds[0]
        embed.set_field_at(1, name="💰 Enchère actuelle", value=f"{auction['price']} €", inline=False)
        embed.set_field_at(2, name="🏆 Meilleur enchérisseur", value=interaction.user.mention, inline=False)

        await auction["message"].edit(embed=embed, view=self)
        await interaction.response.send_message("✅ Mise prise en compte !", ephemeral=True)

# ---------- FIN ENCHÈRE ----------
async def end_auction():
    await asyncio.sleep(auction["duration"] * 60)
    auction["active"] = False

    annonce_channel = bot.get_channel(ANNONCE_CHANNEL_ID)

    if auction["winner"]:
        embed = discord.Embed(
            title="🏁 Enchère terminée",
            description=f"Objet remporté par {auction['winner'].mention} pour **{auction['price']} €**",
            color=discord.Color.gold()
        )
        await annonce_channel.send(embed=embed)

        guild = annonce_channel.guild
        category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            auction["winner"]: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        ticket = await guild.create_text_channel(
            name=f"ticket-{auction['winner'].name}",
            category=category,
            overwrites=overwrites
        )

        await ticket.send(
            f"🎟️ Ticket créé pour {auction['winner'].mention}\n"
            f"Prix final : **{auction['price']} €**"
        )

    auction["message"] = None

# ---------- SLASH COMMAND ----------
@bot.tree.command(name="enchere", description="Lancer une enchère")
@app_commands.describe(prix="Prix de départ", duree="Durée en minutes")
async def enchere(interaction: discord.Interaction, prix: int, duree: int):
    if auction["active"]:
        await interaction.response.send_message("❌ Une enchère est déjà en cours.", ephemeral=True)
        return

    auction["active"] = True
    auction["price"] = prix
    auction["winner"] = None
    auction["duration"] = duree

    embed = discord.Embed(
        title="🔥 Enchère en cours",
        color=discord.Color.blue()
    )
    embed.add_field(name="💰 Prix de départ", value=f"{prix} €", inline=False)
    embed.add_field(name="💰 Enchère actuelle", value=f"{prix} €", inline=False)
    embed.add_field(name="🏆 Meilleur enchérisseur", value="Aucun", inline=False)
    embed.add_field(name="⏱️ Durée", value=f"{duree} minutes", inline=False)

    view = BidButton()
    await interaction.response.send_message(embed=embed, view=view)

    auction["message"] = await interaction.original_response()
    auction["task"] = asyncio.create_task(end_auction())

# ---------- READY ----------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("✅ Bot prêt – commandes synchronisées")

bot.run(TOKEN)
