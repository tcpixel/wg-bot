import discord
from config import *
from discord.ext import commands, tasks
import asyncio

# Initialize bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    daily_cleanup.start()


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

# Run the bot
bot.run(botToken)
