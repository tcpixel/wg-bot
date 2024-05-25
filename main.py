import discord
from config import *
from discord.ext import commands, tasks
import asyncio
import requests
from bs4 import BeautifulSoup

# Initialize bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
allowed_mentions = discord.AllowedMentions.all
lastStatusCode=0

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    daily_cleanup.start()
    ticket_request.start()


#####
# Einkaufsliste
#####
# Nachricht ersetzen und Reaktion hinzufügen
@bot.event
async def on_message(message):
    if str(message.channel.id) == str(groceryListChannelId) and not message.author.bot:
        content = message.content
        await message.delete()
        new_message = await message.channel.send(content)
        await new_message.add_reaction("✅")

# Durchstreichen, falls erledigt
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id != bot.user.id and str(payload.emoji) == "✅" and str(payload.channel_id) == str(groceryListChannelId):
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.edit(content=f"~~{message.content}~~")

# Wieder anpinnen, wenn Reaktion entfernt
@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id != bot.user.id and str(payload.emoji) == "✅" and str(payload.channel_id) == str(groceryListChannelId):
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.edit(content=str(message.content).replace('~~', ''))

# Durchgestrichenes Aufräumen
@tasks.loop(hours=24)
async def daily_cleanup():
    channel = bot.get_channel(int(groceryListChannelId))
    async for message in channel.history():
        if "~~" in message.content:
            await message.delete()


#####
# Summer Breeze
#####
@tasks.loop(minutes=5)
async def ticket_request():
    print("Request wird durchgeführt.")
    channel = bot.get_channel(int(summerBreezeChannelId))
    result = requests.get('https://www.sbtix.de/swp/for/69602-tickets-fruehanreise-slots-dienstag-sinbronn-dinkelsbuehl-am-13-08-2024', verify=False)
    lastStatusCode = result.status_code

    if (lastStatusCode!=200) and (result.status_code!=200):
        content = "@"+ninoUserId+" Es ist ein Fehler aufgetreten. Die Website ist nicht erreichbar.\nStatus Code: "+result.status_code
        await channel.send(content, allowed_mentions=allowed_mentions)
        return 0

    soup = BeautifulSoup(result.content, 'html.parser')
    tabellenZeilen = soup.find_all('tr')
    for zeile in tabellenZeilen:
        spalten = zeile.find_all('td')
        if spalten:
            ticket = str(spalten[0].contents[0])
            if ("Anhängerticket" in ticket) or ("Green Camping" in ticket) or ("Comfort Camping" in ticket):
                continue
            else:
                content = "@everyone Ein neues Ticket ist verfügbar.\n"+ticket+"\nhttps://www.sbtix.de/swp/for/69602-tickets-fruehanreise-slots-dienstag-sinbronn-dinkelsbuehl-am-13-08-2024"
                await channel.send(content, allowed_mentions=allowed_mentions)

    # Zweite Abfrage
    result = requests.get('https://www.sbtix.de/swp', verify=False)

    if (lastStatusCode!=200) and (result.status_code!=200):
        content = "@"+ninoUserId+" Es ist ein Fehler aufgetreten. Die Website ist nicht erreichbar.\nStatus Code: "+result.status_code
        await channel.send(content, allowed_mentions=allowed_mentions)
        return 0

    soup = BeautifulSoup(result.content, 'html.parser')
    tabellenZeilen = soup.find_all('div', 'col-md-3 col-sm-6')
    for zeile in tabellenZeilen:
        if "Frühanreise Slots - Montag" in zeile.contents[0]:
            content = "@everyone Es scheint ein neues Ticket verfügbar zu sein für die Frühanreise am Montag:\n"+str(zeile.contents[0])+"\nhttps://www.sbtix.de/swp\nBitte überprüfen."
            await channel.send(content, allowed_mentions=allowed_mentions)

# Run the bot
bot.run(botToken)
