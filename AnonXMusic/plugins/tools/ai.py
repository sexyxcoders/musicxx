# ai.py
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import openai
import config

# Set your OpenAI API key
openai.api_key = config.OPENAI_API_KEY  # Make sure this is set in your config.py

# Initialize the AI bot
bot = Client(
    "AI_BOT",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# In-memory conversation memory per user
conversation_memory = {}  # {user_id: [messages]}

MAX_MEMORY = 10  # Number of previous messages to remember per user

async def get_ai_response(user_id: int, prompt: str) -> str:
    """Generate AI response using OpenAI with user-specific memory."""
    memory = conversation_memory.get(user_id, [])
    combined_prompt = "\n".join(memory + [f"User: {prompt}", "AI:"])

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=combined_prompt,
            max_tokens=250,
            temperature=0.7,
            stop=["User:", "AI:"]
        )
        answer = response.choices[0].text.strip()
    except Exception as e:
        answer = f"⚠️ Error: {e}"

    # Update memory
    memory.append(f"User: {prompt}")
    memory.append(f"AI: {answer}")
    conversation_memory[user_id] = memory[-MAX_MEMORY*2:]  # Keep last MAX_MEMORY pairs

    return answer

# Start command
@bot.on_message(filters.command("start") & filters.private)
async def start_message(client: Client, message: Message):
    await message.reply_text(
        "👋 Hello! I am your AI bot.\n\n"
        "Use /ai <your message> to chat with me.\n"
        "I can also respond in groups if mentioned!"
    )

# AI chat in private chat
@bot.on_message(filters.command("ai") & filters.private)
async def ai_chat_private(client: Client, message: Message):
    try:
        user_text = message.text.split(None, 1)[1]  # text after /ai
    except IndexError:
        await message.reply_text("Please provide a message. Usage: /ai <message>")
        return

    await message.reply_chat_action("typing")
    answer = await get_ai_response(message.from_user.id, user_text)
    await message.reply_text(f"🤖 AI: {answer}")

# AI reply in groups when bot is mentioned
@bot.on_message(filters.group & filters.text)
async def ai_group_reply(client: Client, message: Message):
    if f"@{bot.username}" in message.text:
        user_text = message.text.replace(f"@{bot.username}", "").strip()
        if not user_text:
            await message.reply_text("Please ask me something after mentioning me.")
            return

        await message.reply_chat_action("typing")
        answer = await get_ai_response(message.from_user.id, user_text)
        await message.reply_text(f"🤖 AI: {answer}", reply_to_message_id=message.message_id)

# Run the bot
if __name__ == "__main__":
    print("🤖 Advanced AI Bot is running...")
    bot.run()