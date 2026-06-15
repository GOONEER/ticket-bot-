import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("TOKEN")
RESULTS_CHANNEL_ID = 1512472772344021113

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ================= CLOSE TICKET =================

class CloseTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Zamknij ticket", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()


# ================= TICKET PANEL =================

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Podanie", style=discord.ButtonStyle.primary)
    async def podanie(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild

        category = discord.utils.get(guild.categories, name="Podania")
        if category is None:
            category = await guild.create_category("Podania")

        channel_name = f"podanie-{interaction.user.name}".lower()

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            channel_name,
            category=category,
            overwrites=overwrites
        )

        await channel.send(
            f"Witaj {interaction.user.mention}\n\n"
            "Wypełnij podanie do LSC:\n\n"
            "- Wiek\n"
            "- Imię\n"
            "- Dlaczego chcesz dołączyć do LSC\n"
            "- Czy masz doświadczenie?\n"
            "- Ile czasu dziennie możesz poświęcić\n"
            "- Jak radzisz sobie z pracą w zespole\n",
            view=CloseTicket()
        )

        await interaction.response.send_message(
            f"Utworzono ticket: {channel.mention}",
            ephemeral=True
        )


# ================= PANEL COMMAND =================

@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):

    embed = discord.Embed(
        title="Podania",
        description="Kliknij przycisk aby stworzyć podanie.",
        color=discord.Color.gold()
    )

    await ctx.send(embed=embed, view=TicketView())


# ================= ACCEPT =================

@bot.tree.command(name="accept", description="Zaakceptuj podanie")
@app_commands.checks.has_permissions(administrator=True)
async def accept(interaction: discord.Interaction):

    member = None
    for overwrite in interaction.channel.overwrites:
        if isinstance(overwrite, discord.Member) and not overwrite.bot:
            member = overwrite
            break

    if not member:
        await interaction.response.send_message("Nie znaleziono użytkownika.", ephemeral=True)
        return

    role1 = interaction.guild.get_role(1512412776952365057)
    role2 = interaction.guild.get_role(1512412776952365059)

    if role1:
        await member.add_roles(role1)
    if role2:
        await member.add_roles(role2)

    embed = discord.Embed(
        title="Zaakceptowane podanie!",
        description=(
            f"{member.mention} Twoje podanie do LSC zostało rozpatrzone pozytywnie!\n\n"
            f"Sprawdził: {interaction.user.mention}"
        ),
        color=discord.Color.green()
    )

    await interaction.channel.send(embed=embed)

    results_channel = interaction.guild.get_channel(RESULTS_CHANNEL_ID)
    if results_channel:
        await results_channel.send(
            f"✔ Podanie zaakceptowane: {member.mention} | Sprawdził: {interaction.user.name}"
        )

    try:
        await member.send(
            "Twoje podanie zostało zaakceptowane.\n\n"
            "Gratulacje — zostałeś przyjęty do LSC.\n\n"
            "Skontaktuj się z administracją."
        )
    except:
        pass

    await interaction.response.send_message("Zaakceptowano.", ephemeral=True)


# ================= DECLINE =================

@bot.tree.command(name="decline", description="Odrzuć podanie")
@app_commands.describe(powod="Powód odrzucenia")
@app_commands.checks.has_permissions(administrator=True)
async def decline(interaction: discord.Interaction, powod: str):

    member = None
    for overwrite in interaction.channel.overwrites:
        if isinstance(overwrite, discord.Member) and not overwrite.bot:
            member = overwrite
            break

    if member:
        try:
            await member.send(
                f"Twoje podanie na LSC zostało odrzucone.\n\nPowód: {powod}"
            )
        except:
            pass

    embed = discord.Embed(
        title="Podanie odrzucone!",
        description=(
            f"{member.mention if member else 'Unknown'} Twoje podanie na LSC zostało odrzucone!\n\n"
            f"Powód: {powod}\n\n"
            f"Sprawdził: {interaction.user.mention}"
        ),
        color=discord.Color.red()
    )

    await interaction.channel.send(embed=embed)

    results_channel = interaction.guild.get_channel(RESULTS_CHANNEL_ID)
    if results_channel:
        await results_channel.send(
            f"❌ Podanie odrzucone: {member.mention if member else 'unknown'} | Powód: {powod} | Sprawdził: {interaction.user.name}"
        )

    await interaction.response.send_message(
        "Odrzucono podanie. Kanał zostanie usunięty za 5 sekund.",
        ephemeral=True
    )

    await asyncio.sleep(5)
    await interaction.channel.delete()


# ================= ON READY =================

@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(TicketView())
    bot.add_view(CloseTicket())
    print(f"Zalogowano jako {bot.user}")


bot.run(TOKEN)
