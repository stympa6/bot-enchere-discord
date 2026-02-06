import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os

TOKEN = os.getenv("TOKEN")  # NE MET JAMAIS LE TOKEN EN DUR

TICKET_CHANNEL_ID = 1468668834667040829  # salon résultat

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


class EnchereView(discord.ui.View):
    def __init__(self, vendeur, prix_depart, duree):
        super().__init__(timeout=duree * 60)
        self.vendeur = vendeur
        self.meilleure_offre = prix_depart
        self.meilleur_offreur = None
        self.terminee = False

    @discord.ui.button(label="💰 Miser +10€", style=discord.ButtonStyle.success)
    async def miser(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.vendeur:
            await interaction.response.send_message(
                "❌ Le vendeur ne peut pas enchérir.",
                ephemeral=True
            )
            return

        if self.terminee:
            await interaction.response.send_message(
                "⏰ L’enchère est terminée.",
                ephemeral=True
            )
            return

        self.meilleure_offre += 10
        self.meilleur_offreur = interaction.user

        await interaction.response.edit_message(
            embed=self.get_embed(),
            view=self
        )

    def get_embed(self):
        embed = discord.Embed(
            title="🔥 Enchère en cours",
            color=discord.Color.gold()
        )
        embed.add_field(name="👤 Vendeur", value=self.vendeur.mention, inline=False)
        embed.add_field(name="💰 Meilleure offre", value=f"{self.meilleure_offre} €", inline=True)

        if self.meilleur_offreur:
            embed.add_field(name="🏆 Meilleur enchérisseur", value=self.meilleur_offreur.mention, inline=True)
        else:
            embed.add_field(name="🏆 Meilleur enchérisseur", value="Aucun", inline=True)

        return embed

    async def on_timeout(self):
        self.terminee = True
        channel = bot.get_channel(TICKET_CHANNEL_ID)

        if channel:
            if self.meilleur_offreur:
                await channel.send(
                    f"🎉 **Enchère terminée**\n"
                    f"👤 Vendeur : {self.vendeur.mention}\n"
                    f"🏆 Gagnant : {self.meilleur_offreur.mention}\n"
                    f"💰 Prix final : **{self.meilleure_offre} €**"
                )
            else:
                await channel.send(
                    f"⏰ **Enchère terminée sans participant**\n"
                    f"👤 Vendeur : {self.vendeur.mention}"
                )


@bot.event
async def on_ready():
    await bot.tree.sync()
    print("✅ Bot prêt avec commandes slash")


@bot.tree.command(name="enchere", description="Créer une enchère avec mises")
@app_commands.describe(
    prix="Prix de départ",
    duree="Durée en minutes"
)
async def enchere(interaction: discord.Interaction, prix: int, duree: int):
    vendeur = interaction.user
    view = EnchereView(vendeur, prix, duree)

    await interaction.response.send_message(
        embed=view.get_embed(),
        view=view
    )


bot.run(TOKEN)
