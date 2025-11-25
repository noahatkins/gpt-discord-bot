import asyncio
import logging
import os
from typing import Dict, List

import discord
from discord import app_commands
from discord.ext import commands

from dotenv import load_dotenv
from services.openai_client import generate_reply

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("bot")

load_dotenv()

SYSTEM_PROMPT = (
    "You are a helpful assistant living in a Discord server. "
    "Respond concisely, keep a friendly tone, and cite code snippets when useful."
)

ThreadHistory = List[Dict[str, str]]
THREAD_CONTEXT: Dict[int, ThreadHistory] = {}


def build_history(prompt: str, user_label: str) -> ThreadHistory:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"{user_label} asked:\n{prompt}",
        },
    ]


intents = discord.Intents.default()
intents.message_content = True
intents.members = False

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def setup_hook() -> None:
    await bot.tree.sync()
    logger.info("Slash commands synced")


@bot.event
async def on_ready() -> None:
    logger.info("Logged in as %s (%s)", bot.user, bot.user and bot.user.id)


@bot.tree.command(name="ask", description="Ask OpenAI a question in a dedicated thread")
@app_commands.describe(prompt="Your question")
async def ask(interaction: discord.Interaction, prompt: str) -> None:
    """Create a thread, send the first OpenAI answer, and keep the context there."""
    if interaction.guild is None or not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message(
            "Please run `/ask` inside a server text channel so I can open a thread.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(thinking=True)

    base_message = await interaction.followup.send(
        f"Creating thread for {interaction.user.mention}...", wait=True
    )
    thread_name = f"{interaction.user.display_name}'s question"
    thread = await interaction.channel.create_thread(
        name=thread_name[:100],
        message=base_message,
        auto_archive_duration=60,
        reason=f"Thread for {interaction.user.display_name}'s /ask command",
    )

    history = build_history(prompt, interaction.user.display_name)
    try:
        reply_text = await generate_reply(history)
    except Exception as exc:
        logger.exception("Failed to fetch OpenAI response")
        await thread.send("I couldn't reach OpenAI. Please try again in a moment.")
        await interaction.followup.send(
            "OpenAI request failed. Check logs for details.", ephemeral=True
        )
        return

    history.append({"role": "assistant", "content": reply_text})
    THREAD_CONTEXT[thread.id] = history

    await thread.send(
        f"{interaction.user.mention} asked:\n> {prompt}\n\n{reply_text}"
    )
    await interaction.followup.send(
        f"Thread <#{thread.id}> is ready. Continue the conversation there!",
        ephemeral=True,
    )


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user:
        return

    await bot.process_commands(message)

    if not isinstance(message.channel, discord.Thread):
        return

    history = THREAD_CONTEXT.get(message.channel.id)
    if history is None or message.author.bot:
        return

    history.append(
        {
            "role": "user",
            "content": f"{message.author.display_name} said:\n{message.content}",
        }
    )

    try:
        async with message.channel.typing():
            reply_text = await generate_reply(history)
    except Exception:
        logger.exception("Failed to continue conversation")
        await message.channel.send(
            "I hit an error while contacting OpenAI. Please try again later."
        )
        history.pop()  # remove the user message to avoid duplication
        return

    history.append({"role": "assistant", "content": reply_text})
    await message.channel.send(reply_text)


@bot.event
async def on_thread_remove(thread: discord.Thread) -> None:
    THREAD_CONTEXT.pop(thread.id, None)


@bot.event
async def on_thread_delete(thread: discord.Thread) -> None:
    THREAD_CONTEXT.pop(thread.id, None)


def main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN environment variable is missing")

    bot.run(token)


if __name__ == "__main__":
    main()

