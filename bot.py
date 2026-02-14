import discord
from discord.ext import commands
import asyncio

# =======================
# CONFIG
# =======================
TOKEN = ""

TICKET_CATEGORY_ID = 1468668766924832861
STAFF_ROLE_ID = 111111111111111111
SECOND_ROLE_ID = 1468706115096416286
PING_ROLE_ID = 1471205818794770483

MAX_MANUAL_BID = 1000  # 10€

# =======================
# BOT
# =======================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
members_intent = discord.Intents.members
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

auctions = {}

# =======================
# DATA STRUCTURE
# =======================
def new_auction():
    return {
        "message": None,
        "title": "",
        "image": None,  # IMAGE UPLOAD
        "highest_bid": 0,
        "highest_bidder": None,
        "last_outbid": None,
        "followers": set(),
        "owner": None,
        "remaining": 0
    }

# =======================
# EMBED
# =======================
def build_embed(a):
    embed = discord.Embed(
        title=f"🧾 ENCHÈRE — {a['title']}",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="💶 Meilleure offre",
        value=f"**{a['highest_bid']/100:.2f} €**",
        inline=True
    )

    embed.add_field(
        name="⏳ Temps restant",
        value=f"{a['remaining']//60:02d}:{a['remaining']%60:02d}",
        inline=True
    )

    embed.add_field(
        name="👤 Enchérisseur",
        value=a["highest_bidder"].mention if a["highest_bidder"] else "Aucun",
        inline=False
    )

    embed.add_field(
        name="🔔 Dernier dépassé",
        value=a["last_outbid"].mention if a["last_outbid"] else "—",
        inline=False
    )

    embed.add_field(
        name="👀 Suiveurs",
        value=str(len(a["followers"])),
        inline=False
    )

    if a["image"]:
        embed.set_image(url=a["image"])

    embed.set_footer(text="Mise manuelle max 10€ • Boutons illimités")
    return embed

# =======================
# VIEW
# =======================
class BidView(discord.ui.View):
    def __init__(self, channel_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    async def notify_followers(self, bidder, amount):
        auction = auctions[self.channel_id]
        for uid in auction["followers"]:
            if uid == bidder.id:
                continue
            try:
                user = await bot.fetch_user(uid)
                await user.send(
                    f"🔔 **Nouvelle enchère !**\n\n"
                    f"🧾 {auction['title']}\n"
                    f"💰 {amount/100:.2f} €\n"
                    f"👤 {bidder.mention}"
                )
            except:
                pass

    async def apply_bid(self, interaction, new_bid):
        auction = auctions[self.channel_id]

        if new_bid <= auction["highest_bid"]:
            return await interaction.response.send_message(
                "❌ Mise trop basse",
                ephemeral=True
            )

        old_bidder = auction["highest_bidder"]

        auction["highest_bid"] = new_bid
        auction["highest_bidder"] = interaction.user
        auction["last_outbid"] = old_bidder if old_bidder and old_bidder != interaction.user else None

        await auction["message"].edit(embed=build_embed(auction), view=self)

        if auction["last_outbid"]:
            try:
                await auction["last_outbid"].send(
                    f"🔔 Tu viens d’être dépassé sur **{auction['title']}** !"
                )
            except:
                pass

        await self.notify_followers(interaction.user, new_bid)

        await interaction.response.send_message(
            f"✅ Mise acceptée : **{new_bid/100:.2f}€**",
            ephemeral=True
        )

    # ===== BOUTONS =====
    @discord.ui.button(label="+0.20€", style=discord.ButtonStyle.primary)
    async def b20(self, i, _):
        await self.apply_bid(i, auctions[self.channel_id]["highest_bid"] + 20)

    @discord.ui.button(label="+0.50€", style=discord.ButtonStyle.primary)
    async def b50(self, i, _):
        await self.apply_bid(i, auctions[self.channel_id]["highest_bid"] + 50)

    @discord.ui.button(label="+1€", style=discord.ButtonStyle.success)
    async def b1(self, i, _):
        await self.apply_bid(i, auctions[self.channel_id]["highest_bid"] + 100)

    @discord.ui.button(label="+2€", style=discord.ButtonStyle.success)
    async def b2(self, i, _):
        await self.apply_bid(i, auctions[self.channel_id]["highest_bid"] + 200)

    @discord.ui.button(label="+5€", style=discord.ButtonStyle.danger)
    async def b5(self, i, _):
        await self.apply_bid(i, auctions[self.channel_id]["highest_bid"] + 500)

    @discord.ui.button(label="💰 Mise libre", style=discord.ButtonStyle.secondary)
    async def free(self, i, _):
        await i.response.send_modal(BidModal(self.channel_id, self))

    @discord.ui.button(label="👀 Suivre / Stop", style=discord.ButtonStyle.secondary)
    async def follow(self, i, _):
        auction = auctions[self.channel_id]

        if i.user.id in auction["followers"]:
            auction["followers"].remove(i.user.id)
            msg = "❌ Tu ne suis plus l’enchère"
        else:
            auction["followers"].add(i.user.id)
            msg = "✅ Tu suis l’enchère"

        await auction["message"].edit(embed=build_embed(auction), view=self)
        await i.response.send_message(msg, ephemeral=True)

# =======================
# MODAL
# =======================
class BidModal(discord.ui.Modal, title="Mise libre"):
    amount = discord.ui.TextInput(label="Montant (€)")

    def __init__(self, cid, view):
        super().__init__()
        self.cid = cid
        self.view = view

    async def on_submit(self, i):
        bid = int(float(self.amount.value.replace(",", ".")) * 100)

        if bid > MAX_MANUAL_BID:
            return await i.response.send_message(
                "❌ Maximum 10€ par saisie. Utilise les boutons pour monter plus haut.",
                ephemeral=True
            )

        await self.view.apply_bid(i, bid)

# =======================
# TICKET
# =======================
async def create_ticket(guild, seller, buyer, title, amount):
    category = guild.get_channel(TICKET_CATEGORY_ID)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        seller: discord.PermissionOverwrite(view_channel=True),
        buyer: discord.PermissionOverwrite(view_channel=True),
        guild.me: discord.PermissionOverwrite(view_channel=True)
    }

    for rid in (STAFF_ROLE_ID, SECOND_ROLE_ID):
        role = guild.get_role(rid)
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True)

    channel = await guild.create_text_channel(
        name=f"ticket-{buyer.name}",
        category=category,
        overwrites=overwrites
    )

    await channel.send(
        f"🎟️ **TICKET D’ENCHÈRE**\n\n"
        f"🧾 Objet : {title}\n"
        f"🏆 Gagnant : {buyer.mention}\n"
        f"💰 Montant final : **{amount/100:.2f}€**\n\n"
        f"Merci de finaliser ici."
    )

# =======================
# START
# =======================
@bot.command()
async def start(ctx, titre: str, prix: float, duree: int):

    auction = new_auction()

    # ===== IMAGE UPLOAD AUTOMATIQUE =====
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.content_type and attachment.content_type.startswith("image"):
            auction["image"] = attachment.url

    auction.update({
        "title": titre,
        "highest_bid": int(prix * 100),
        "owner": ctx.author,
        "remaining": duree * 60
    })

    auctions[ctx.channel.id] = auction
    view = BidView(ctx.channel.id)

    msg = await ctx.send(
        content=ctx.guild.get_role(PING_ROLE_ID).mention,
        embed=build_embed(auction),
        view=view
    )

    auction["message"] = msg
    await ctx.message.delete()

    while auction["remaining"] > 0:
        await asyncio.sleep(1)
        auction["remaining"] -= 1
        await msg.edit(embed=build_embed(auction))

    await msg.edit(view=None)

    if auction["highest_bidder"]:
        end_msg = await ctx.send(
            f"🏆 **ENCHÈRE TERMINÉE**\n"
            f"Gagnant : {auction['highest_bidder'].mention}\n"
            f"Montant : **{auction['highest_bid']/100:.2f}€**"
        )

        await create_ticket(
            ctx.guild,
            auction["owner"],
            auction["highest_bidder"],
            auction["title"],
            auction["highest_bid"]
        )

        await asyncio.sleep(60)
        await end_msg.delete()

    await msg.delete()
    auctions.pop(ctx.channel.id, None)

# =======================
# READY
# =======================
@bot.event
async def on_ready():
    print("✅ Bot prêt")

bot.run(TOKEN)
