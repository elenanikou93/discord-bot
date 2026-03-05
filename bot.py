import asyncio
from openai import OpenAI
import random
import discord
import os
from dotenv import load_dotenv

# φορτώνει το .env αρχείο (τοπικά). Στο Railway παίρνει variables από το environment.
load_dotenv()

# παίρνει το token από το environment
TOKEN = os.getenv("DISCORD_TOKEN")

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"

ROASTS = [
    "I'd explain it to you, but I forgot my crayons.",
    "You're not useless, you could be used as a bad example.",
    "You have the confidence of someone who has never checked their code.",
    "If laziness were a programming language, you'd be fluent.",
    "Your brain has too many background processes and none of them useful."
    "My AI brain just crashed but you're still roasted.",
    "Even without AI I can tell you're a bug."
]

# επιτρέπει στο bot να διαβάζει messages
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


def _sync_generate_roast(target_display: str) -> str:
    system = (
        "You are Kado, a chaotic, funny Discord roast bot. "
        "Keep it playful and witty. 1-2 short sentences max. "
        "No slurs, no hate, no harassment of protected groups."
    )

    prompt = f"Roast {target_display}."

    resp = openai_client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_output_tokens=80,
    )
    return resp.output_text.strip()


async def generate_roast(target_display: str) -> str:
    return await asyncio.to_thread(_sync_generate_roast, target_display)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == "!ping":
        await message.channel.send("pong")
        return

    if message.content.startswith("!roast"):
        # αν υπάρχει mention, πάρε το πρώτο, αλλιώς roast τον author
        target = message.mentions[0] if message.mentions else message.author

        try:
            roast = await generate_roast(target.display_name)
            if not roast:
                roast = random.choice(ROASTS)
        except Exception:
            roast = random.choice(ROASTS)

        await message.channel.send(f"{target.mention} {roast}")
        return


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


client.run(TOKEN)