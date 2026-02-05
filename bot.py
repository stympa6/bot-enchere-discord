import discord
from discord import app_commands
from discord.ext import commands
import asyncio

TOKEN = ""
TICKET_CHANNEL_ID = 1468668834667040829

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

class EnchereView(discord.ui.View):
    def __init__(self, vendeur):
        super().__init__(timeout=None)
        self.vendeur = vendeur
        self.participants = []

    @discord.ui.button(label="Je participe", style=discord.ButtonStyle.success)
    async def participer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participants:
            self.participants.append(interaction.user)
            await interaction.response.send_message("✅ Participation enregistrée", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Tu participes déjà", ephemeral=True)

    @discord.ui.button(label="Je participe pas", style=discord.ButtonStyle.secondary)
    async def refuser(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participants:
            self.participants.remove(interaction.user)
        await interaction.response.send_message("❌ Tu ne participes plus", ephemeral=True)

    @discord.ui.button(label="Contacter l’annonceur", style=discord.ButtonStyle.primary)
    async def contacter(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"📩 Annonceur : {self.vendeur.mention}",
            ephemeral=True
        )

    @discord.ui.button(label="Plus d’info", style=discord.ButtonStyle.secondary)
    async def info(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "ℹ️ Enchère en cours. Clique sur *Je participe* pour entrer.",
            ephemeral=True
        )

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("✅ Bot prêt avec commandes slash")

@bot.tree.command(name="enchere", description="Créer une enchère")
@app_commands.describe(prix="Prix de départ", duree="Durée en minutes")
async def enchere(interaction: discord.Interaction, prix: int, duree: int):
    vendeur = interaction.user
    view = EnchereView(vendeur)

    embed = discord.Embed(
        title="🔥 Nouvelle enchère",
        description=(
            f"👤 Annonceur : {vendeur.mention}\n"
            f"💰 Prix de départ : **{prix}€**\n"
            f"⏱️ Durée : **{duree} minutes**"
        ),
        color=discord.Color.gold()
    )

    await interaction.response.send_message(embed=embed, view=view)

    await asyncio.sleep(duree * 60)

    ticket_channel = bot.get_channel(TICKET_CHANNEL_ID)
    if ticket_channel:
        if view.participants:
            acheteur = view.participants[0]
            await ticket_channel.send(
                f"🎉 **Enchère terminée**\n"
                f"👤 Vendeur : {vendeur.mention}\n"
                f"🛒 Acheteur : {acheteur.mention}\n"
                f"💰 Prix : {prix}€"
            )
        else:
            await ticket_channel.send("⏰ Enchère terminée sans participant")

bot.run(TOKEN)
