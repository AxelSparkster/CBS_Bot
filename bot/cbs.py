import bson
import discord
import logging
import os
from discord.ext import commands
from dotenv import load_dotenv

# local imports
import bot.exts.database as database
from bot.exts.cogs.administrative import AdministrativeCog
from bot.exts.cogs.animal import AnimalsCog
from bot.exts.cogs.messagedetection import MessageDetectionCog
from bot.exts.cogs.sdvxplus import SdvxPlusCog
from bot.exts.cogs.sdvxindex import SdvxindexCog
from bot.exts.cogs.threeicecream import ThreeIceCreamCog
from bot.utils.detectionutils import check_message_for_matches


# Discord bot related junk
INTENTS = discord.Intents.default()
INTENTS.messages = True
INTENTS.message_content = True
DISCORD_CLIENT = commands.Bot(command_prefix="$cbs ", intents=INTENTS)


@DISCORD_CLIENT.event
async def on_message(message):
    ctx = await DISCORD_CLIENT.get_context(message)

    # Always ignore bot messages
    if ctx.message.author.bot:
        return

    # Check to see if we're allowed to send the message first
    if not await can_message(ctx):
        return

    # See if the user has said any "key terms".
    await check_message_for_matches(ctx)

    # Otherwise, process any bot commands normally using the discord.py library.
    await DISCORD_CLIENT.process_commands(ctx.message)


async def can_message(ctx):
    # The bot owner or admin should always be able to run commands
    if await ctx.bot.is_owner(ctx.author) or ctx.permissions.administrator:
        return True

    # Check if we're allowed to send the message in the server
    return database.get_bot_messages_ability(ctx.message.guild.id)


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
    load_dotenv()
    await DISCORD_CLIENT.add_cog(AnimalsCog(DISCORD_CLIENT))
    await DISCORD_CLIENT.add_cog(AdministrativeCog(DISCORD_CLIENT))
    await DISCORD_CLIENT.add_cog(MessageDetectionCog(DISCORD_CLIENT))
    await DISCORD_CLIENT.add_cog(SdvxindexCog(DISCORD_CLIENT))
    await DISCORD_CLIENT.add_cog(SdvxPlusCog(DISCORD_CLIENT))
    await DISCORD_CLIENT.add_cog(ThreeIceCreamCog(DISCORD_CLIENT))
    DISCORD_CLIENT.run(os.getenv('TOKEN'))

