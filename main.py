import discord
from config import *
from discord.ext import commands, tasks
import asyncio
import requests
from bs4 import BeautifulSoup
import urllib3
import os
import random
import shutil
from datetime import datetime, timedelta

urllib3.disable_warnings()

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
    racoonpics.start()


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
    allowed_mentions = discord.AllowedMentions(everyone = True)
    channel = bot.get_channel(int(summerBreezeChannelId))
    # result = requests.get('https://www.sbtix.de/swp/for/69602-tickets-fruehanreise-slots-dienstag-sinbronn-dinkelsbuehl-am-13-08-2024', verify=False)
    # lastStatusCode = result.status_code

    # if result.status_code == 404:
    #     return 0
    # if (lastStatusCode!=200) and (result.status_code!=200):
    #     print("Website Fehler")
    #     content = "@"+ninoUserId+" Es ist ein Fehler aufgetreten. Die Website ist nicht erreichbar.\nStatus Code: "+result.status_code
    #     await channel.send(content, allowed_mentions=allowed_mentions)
    #     return 0

    # soup = BeautifulSoup(result.content, 'html.parser')
    # tabellenZeilen = soup.find_all('tr')
    # for zeile in tabellenZeilen:
    #     spalten = zeile.find_all('td')
    #     if spalten:
    #         ticket = str(spalten[0].contents[0])
    #         if ("Anhängerticket" in ticket) or ("Green Camping" in ticket) or ("Comfort Camping" in ticket) or ("Reserved" in ticket) or ("19:00" in ticket):  
    #             continue
    #         else:
    #             print("Ticket gefunden: "+ticket)
    #             content = "@everyone 🟩 Ein neues Dienstag Ticket ist verfügbar.\n"+ticket+"\nhttps://www.sbtix.de/swp/for/69602-tickets-fruehanreise-slots-dienstag-sinbronn-dinkelsbuehl-am-13-08-2024"
    #             await channel.send(content, allowed_mentions=allowed_mentions)

    # Zweite Abfrage (Montag)
    result = requests.get('https://www.sbtix.de/swp/for/69706-tickets-fruehanreise-slots-montag-sinbronn-dinkelsbuehl-am-12-08-2024', verify=False)

    if result.status_code == 404:
        return 0
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
            if ("Anhängerticket" in ticket) or ("Green Camping" in ticket) or ("Comfort Camping" in ticket) or ("Reserved" in ticket):  
                continue
            else:
                print("Ticket gefunden: "+ticket)
                content = "@everyone 🟥 Ein neues **Montag*** Ticket ist verfügbar.\n"+ticket+"\nhttps://www.sbtix.de/swp/for/69602-tickets-fruehanreise-slots-dienstag-sinbronn-dinkelsbuehl-am-13-08-2024"
                await channel.send(content, allowed_mentions=allowed_mentions)


#####
# Racoon of the Day
#####
@tasks.loop(hours=1)
async def racoonpics():
    if (datetime.now().weekday() == 0) and (datetime.now().hour == 7): #hour 7 = hour 9 (UTC+2)
        print(str(datetime.now())+" "+str(datetime.now())+" - Racoon of the week wird gepostet.")
        channel = bot.get_channel(int(racoonPicsChannelId))
        logChannel = bot.get_channel(int(botLogChannelId))
        meme_files = [f for f in os.listdir('./racoonpics') if os.path.isfile(os.path.join('./racoonpics', f))]
        if not meme_files:
            await channel.send("Diese Woche leider kein Waschbär 🥲")
            return

        selected_meme = random.choice(meme_files)
        meme_path = os.path.join('./racoonpics', selected_meme)
        await channel.send(file=discord.File(meme_path))
        # Move the posted meme to the 'posted' folder
        shutil.move(meme_path, os.path.join('./racoonpics/posted/', selected_meme))

        if len(meme_files) <= 6:
            await logChannel.send("Warnung, nur noch "+str(len(meme_files)-1)+" Waschbär-Bilder im Ordner.")



# Run the bot
bot.run(botToken)
