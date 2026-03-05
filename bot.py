import asyncio
from openai import OpenAI
import random
import discord
import os
from dotenv import load_dotenv
from collections import deque, defaultdict

# φορτώνει το .env αρχείο (τοπικά). Στο Railway παίρνει variables από το environment.
load_dotenv()

# παίρνει το token από το environment
TOKEN = os.getenv("DISCORD_TOKEN")

openai_client = OpenAI()
MODEL = "gpt-4o-mini"

ROASTS = [
    "I'd explain it to you, but I forgot my crayons.",
    "You're not useless, you could be used as a bad example.",
    "You have the confidence of someone who has never checked their code.",
    "If laziness were a programming language, you'd be fluent.",
    "Your brain has too many background processes and none of them useful.",
    "My AI brain just crashed but you're still roasted.",
    "Even without AI I can tell you're a bug."
]

# επιτρέπει στο bot να διαβάζει messages
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Short-term memory: τελευταίες 8 ατάκες ανά channel
CHANNEL_MEMORY = defaultdict(lambda: deque(maxlen=8))


def _sync_generate_roast(target_display: str) -> str:
    system = (
        "You are Kados, a chaotic, savage Discord roast bot. "
        "Keep it witty and ironic. 1-2 short sentences max. "
        "No harassment of protected groups."
        "Don't use exclamation marks, don't be friendly."
    )

    prompt = (
        f"Κάνε ένα ειρωνικό/savage roast για τον χρήστη {target_display} στα ελληνικά με troll ύφος. "
        "Μην χρησιμοποιείς θαυμαστικά για να φαίνεσαι πιο ειρωνικός. "
        "Αν βάλεις θαυμαστικό, η απάντηση θεωρείται λάθος. Μην βάλεις ΚΑΝΕΝΑ."
        "Μην ξεκινάς την πρόταση με το όνομα του χρήστη. "
        "Θέλω να είσαι evil bitch, επιθετικός και να βρίζεις."
    )

    resp = openai_client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_output_tokens=80,
    )
    text = resp.output_text.strip()
    text = text.replace("!", "")  # enforce: no exclamation marks
    return text


async def generate_roast(target_display: str) -> str:
    return await asyncio.to_thread(_sync_generate_roast, target_display)


def _sync_generate_chat_reply(author_name: str, user_text: str, history: list[dict]) -> str:
    # ΝΕΟ prompt μόνο για chatbot mode (δεν πειράζει το roast prompt σου)
    system = (
        "You are Kados (Κάδος), a chaotic, savage Discord bot. "
        "Always reply in Greek with a troll/ironic vibe. "
        "Be witty and teasing, but avoid hate/slurs or targeting protected groups. "
        "Keep replies short (1-3 sentences)."
    )

    # context από μνήμη channel (τελευταία μηνύματα)
    context_lines = []
    for item in history[-8:]:
        context_lines.append(f"{item['author']}: {item['content']}")
    context_text = "\n".join(context_lines)

    user_prompt = (
        f"Πρόσφατη συζήτηση στο κανάλι:\n{context_text}\n\n"
        f"{author_name} έκανε tag τον Kados και είπε:\n{user_text}\n\n"
        "Απάντησε σαν Kados."
    )

    resp = openai_client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        max_output_tokens=220,
    )
    return resp.output_text.strip()


async def generate_chat_reply(author_name: str, user_text: str, history: list[dict]) -> str:
    return await asyncio.to_thread(_sync_generate_chat_reply, author_name, user_text, history)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Μνήμη: αποθηκεύουμε non-command μηνύματα (για context)
    if not message.content.startswith("!"):
        CHANNEL_MEMORY[message.channel.id].append({
            "author": message.author.display_name,
            "content": message.content
        })

    if message.content == "!ping":
        await message.channel.send("pong")
        return

    # 1) Roast command
    if message.content.startswith("!roast"):
        # αν υπάρχει mention, πάρε το πρώτο, αλλιώς roast τον author
        target = message.mentions[0] if message.mentions else message.author

        try:
            roast = await generate_roast(target.display_name)
            if not roast:
                roast = random.choice(ROASTS)
        except Exception as e:
            print("OPENAI ROAST ERROR:", e)
            roast = random.choice(ROASTS)

        await message.channel.send(f"{target.mention} {roast}")
        return

    # 2) Chatbot mode: απαντάει όταν τον κάνουν mention (@Kados)
    if client.user in message.mentions:
        # βγάζουμε το mention του bot από το κείμενο
        user_text = (
            message.content
            .replace(f"<@{client.user.id}>", "")
            .replace(f"<@!{client.user.id}>", "")
            .strip()
        )

        if not user_text:
            await message.channel.send("Ναι; 😈 Γράψε κάτι, μη με κάνεις tag για decor.")
            return

        history = list(CHANNEL_MEMORY[message.channel.id])

        try:
            reply = await generate_chat_reply(
                author_name=message.author.display_name,
                user_text=user_text,
                history=history
            )
            if not reply:
                reply = "Κόλλησα. Πες το αλλιώς."
        except Exception as e:
            print("OPENAI CHAT ERROR:", e)
            reply = "Κάτι έπαθε ο εγκέφαλός μου. Δοκίμασε ξανά. 🗑️"

        await message.channel.send(reply)
        return


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


client.run(TOKEN)