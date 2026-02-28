import random
import discord
import os
from dotenv import load_dotenv

# φορτώνει το .env αρχείο
load_dotenv()

# παίρνει το token από το environment
TOKEN = os.getenv("DISCORD_TOKEN")

ROASTS = [
    "I'd explain it to you, but I forgot my crayons.",
    "You're not useless, you could be used as a bad example.",
    "You have the confidence of someone who has never checked their code.",
    "If laziness were a programming language, you'd be fluent.",
    "Your brain has too many background processes and none of them useful."
]

# επιτρέπει στο bot να διαβάζει messages
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == "!ping":
        await message.channel.send("pong")

    if message.content.startswith("!roast"):
        roast = random.choice(ROASTS)

    # αν υπάρχει mention, πάρε το πρώτο
    if message.mentions:
        target = message.mentions[0]
    else:
        target = message.author

    await message.channel.send(f"{target.mention} {roast}")

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

client.run(TOKEN)