import asyncio
import bson
import discord
import logging
import nest_asyncio
import os
from discord.ext import commands

# local imports
import exts.database as database
from exts.cogs.administrative import AdministrativeCog
from exts.cogs.animal import AnimalsCog
from exts.cogs.messagedetection import MessageDetectionCog
from utils.detection import check_message_for_matches

# Needed since asyncio by itself has trouble running main() due to the event
# listener being too busy and causes a "asyncio.run() cannot be called from a running event loop"
# error.
nest_asyncio.apply()

# Discord bot related junk
INTENTS = discord.Intents.default()
INTENTS.messages = True
INTENTS.message_content = True
DISCORD_CLIENT = commands.Bot(command_prefix="$cbs ", intents=INTENTS)


@DISCORD_CLIENT.event
async def on_message(message):
    ctx = await DISCORD_CLIENT.get_context(message)

    # Check to see if we're allowed to send the message first
    if not await can_message(ctx):
        return

    # Always ignore bot messages
    if ctx.message.author.bot:
        return

    # See if the user has said any "key terms".
    await check_message_for_matches(ctx)

    # Otherwise, process any bot commands normally using the discord.py library.
    await DISCORD_CLIENT.process_commands(ctx.message)


async def can_message(ctx):
    # The bot owner or admin should always be able to run commands
    if await ctx.bot.is_owner(ctx.author) or ctx.message.author.guild_permissions.administrator:
        return True

    # Check if we're allowed to send the message in the server
    guild_settings = database.SETTINGS_COLLECTION.find({"guild_id": bson.int64.Int64(ctx.message.guild.id)}).limit(
        1).next()
    if not guild_settings["message_enabled"]:
        logging.warning(f"Message blocked from being sent for {ctx.message.guild.id} due to messages being disabled.")
        return False

    return True


@DISCORD_CLIENT.event
async def on_ready():
    logging.warning(f"CBS Bot has started.")
    await DISCORD_CLIENT.change_presence(activity=discord.Game('MAX 300 on repeat'))


@DISCORD_CLIENT.event
async def on_guild_join(guild: discord.Guild):
    # If we don't have an existing setting record for this guild, insert defaults
    if not database.has_guild_settings(guild.id):
        database.insert_default_guild_settings(guild.id)


async def main():
    await DISCORD_CLIENT.add_cog(AnimalsCog(DISCORD_CLIENT))
    await DISCORD_CLIENT.add_cog(AdministrativeCog(DISCORD_CLIENT))
    await DISCORD_CLIENT.add_cog(MessageDetectionCog(DISCORD_CLIENT))
    DISCORD_CLIENT.run(os.environ['TOKEN'])

asyncio.run(main())
