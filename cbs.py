
from typing import Literal
import bson
import datetime
import discord
import logging
import os
import pymongo
import re
import requests
import sys
import time
import urllib.parse
from dateutil import tz
from discord.ext import commands
from enum import IntEnum
from unidecode import unidecode

# Discord bot related junk
INTENTS = discord.Intents.default()
INTENTS.messages = True
INTENTS.message_content = True
DISCORD_CLIENT = commands.Bot(command_prefix = "$cbs ", intents=INTENTS)

# MongoDB related junk
MONGO_CLIENT = pymongo.MongoClient((f'mongodb://{urllib.parse.quote_plus(os.getenv("MONGODB_USERNAME"))}' +
                                    f':{urllib.parse.quote_plus(os.getenv("MONGODB_PASSWORD"))}' +
                                    f'@mongo:27017/{os.getenv("MONGODB_DATABASE")}?authSource=admin'))
CBS_DATABASE = MONGO_CLIENT["cbs-database"]
MESSAGE_COLLECTION = CBS_DATABASE["message-collection"]
SETTINGS_COLLECTION = CBS_DATABASE["settings-collection"]

# Models (TODO: move into a models class later)
class MatchType(IntEnum):
    NO_MATCH = 0
    CBS = 1
    ROUNDONE = 2

# Constants
CBS_REGEX = "(?i)combo.*based|based.*combo"
R1_REGEX = "(?i)(round1|r1|round one|round 1).*(mn|minnesota)|(mn|minnesota).*(round1|r1|round one|round 1)"
SECS_IN_A_DAY = 86400
SECS_IN_A_HOUR = 3600
SECS_IN_A_MIN = 60

# Extra stuff
CBS_COOLDOWN = commands.CooldownMapping.from_cooldown(2, 86400, commands.BucketType.user)
ANIMAL_LITERAL = Literal["fox", "yeen", "dog", "snek", "poss", "leo", "serval", "bleat",
"shiba", "racc", "dook", "ott", "snep", "woof", "capy", "bear", "bun",
"caracal", "puma", "mane", "marten", "tig", "skunk", "jaguar", "yote"]

def s(time_unit) -> str:
    # Decides whether or not the given time unit needs an "s" after its declaration
    return "s" if time_unit != 1 else ""

def is_match(message):
    # There's a match if the enum's int value is 0 or better. TODO: Is there a better way to do this?
    return (int(get_match_type(message)) > 0)

def get_match_type(message) -> MatchType:
    # Figure out what type of match the message has
    if (re.search(CBS_REGEX, unidecode(message.content))):
        return MatchType.CBS
    elif (re.search(R1_REGEX, unidecode(message.content))):
        return MatchType.ROUNDONE
    else:
        return MatchType.NO_MATCH
    
def get_match_initmessage(match_type) -> str:
    if match_type == MatchType.CBS:
        return "Someone just mentioned combo based scoring for the first time!"
    elif match_type == MatchType.ROUNDONE:
        return "Someone just mentioned Round 1 being in Minnesota for the first time!"
    else:
        logging.warning("Unknown match type.")

def get_match_message(match_type, timestring) -> str:
    if match_type == MatchType.CBS:
        return f"Combo-based scoring was last mentioned {timestring} ago. The timer has been reset."
    elif match_type == MatchType.ROUNDONE:
        return f"Round 1 being in Minnesota was last mentioned {timestring} ago. The timer has been reset."
    else:
        logging.warning("Unknown match type.")
    

def format_timedelta(delta: datetime.timedelta) -> str:
    # Gets the number of days/hours/minutes/seconds in a user-readable string from a timedelta
    # Loosely based off of Miguendes' code here: https://miguendes.me/how-to-use-datetimetimedelta-in-python-with-examples
    seconds = int(delta.total_seconds())
    days, seconds = divmod(seconds, SECS_IN_A_DAY)
    hours, seconds = divmod(seconds, SECS_IN_A_HOUR)
    minutes, seconds = divmod(seconds, SECS_IN_A_MIN)

    return f"{days} day{s(days)}, {hours} hour{s(hours)}, {minutes} minute{s(minutes)} and {seconds} second{s(seconds)}"

def convert_to_unix_time(date: datetime.datetime) -> str:
    return f'<t:{str(time.mktime(date.timetuple()))[:-2]}:R>'

def get_script_directory() -> str:
    return os.path.dirname(os.path.abspath(sys.argv[0]))

def get_random_animal_image(animal: str) -> str:
    # Gets URL of random animal image.
    params = {'animal': animal}
    response = requests.get("https://api.tinyfox.dev/img.json", params)
    animal_url = "https://api.tinyfox.dev" + response.json().get("loc")
    return animal_url

@DISCORD_CLIENT.hybrid_command(name="sync", description="(Owner/Admin only) Syncs the command tree.")
async def sync(ctx) -> None:
    if await ctx.bot.is_owner(ctx.author) or await ctx.message.author.guild_permissions.administrator:
        await DISCORD_CLIENT.tree.sync()
        logging.warning("Command tree synced.")
        await ctx.send("Command tree synced.")

@DISCORD_CLIENT.hybrid_command(name="shutup", description="(Owner/Admin only) Disables the bot from messaging in the server.")
async def shutup(ctx) -> None:
    if await ctx.bot.is_owner(ctx.author) or await ctx.message.author.guild_permissions.administrator:
        logging.warning(f"Disabling messages for guild ID {ctx.message.guild.id}.")
        SETTINGS_COLLECTION.update_one({"guild_id": bson.int64.Int64(ctx.message.guild.id)}, {"$set": { "message_enabled": False }})
        await ctx.send("Messages have been disabled.")

@DISCORD_CLIENT.hybrid_command(name="getupanddanceman", description="(Owner/Admin only) Reenables the bot's ability to message in the server.")
async def getupanddanceman(ctx) -> None:
    if await ctx.bot.is_owner(ctx.author) or await ctx.message.author.guild_permissions.administrator:
        logging.warning(f"Enabling messages for guild ID {ctx.message.guild.id}.")
        SETTINGS_COLLECTION.update_one({"guild_id": bson.int64.Int64(ctx.message.guild.id)}, {"$set": { "message_enabled": True }})
        await ctx.send("Messages have been enabled.")

@DISCORD_CLIENT.hybrid_command(name="lastmessage", description="Gets information about the last time combo-based scoring was mentioned. 1 time/user/day.")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def lastmessage(ctx) -> None:
    # Get details of last message
    #
    last_cbs_message = MESSAGE_COLLECTION.find({"guild_id": bson.int64.Int64(ctx.message.guild.id)}).sort({"created_at": -1}).limit(1).next()
    last_cbs_message_link = f'https://canary.discord.com/channels/{last_cbs_message["guild_id"]}/{last_cbs_message["channel_id"]}/{last_cbs_message["message_id"]}'
    preface_message = (f'The last mention of combo-based scoring was {convert_to_unix_time(last_cbs_message["created_at"])} by '
                       f'<@{last_cbs_message["author_id"]}>, which was here: {last_cbs_message_link}\n\n')
    localized_date = last_cbs_message["created_at"].replace(tzinfo=tz.gettz('UTC')).astimezone(tz.gettz('America/Chicago'))

    # Create the message embed
    #
    embed = discord.Embed(color=discord.Color.red())
    embed.set_author(name=f'{last_cbs_message["author"]}', icon_url=f'{last_cbs_message["avatar_url"]}')
    embed.add_field(name='Message', value=f'{last_cbs_message["message"]}', inline=False)
    embed.add_field(name='Date', value=f'{localized_date.strftime("%B %d, %Y %I:%M %p %Z%z")}', inline=False)
    embed.set_footer(text="Note: This message is sent silently and does not ping users.")

    await ctx.send(content=f'{preface_message}', embed=embed, silent=True)

@DISCORD_CLIENT.hybrid_command(name="possum", description="Get a random possum image. 2 times/user/day.")
@commands.cooldown(2, 86400, commands.BucketType.user)
async def possum(ctx) -> None:
    await ctx.send(get_random_animal_image("poss"))

@DISCORD_CLIENT.hybrid_command(name="randomanimal", description="Get a random animal image. 1 time/user/day.")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def random_animal(ctx, animal: ANIMAL_LITERAL) -> None:
    await ctx.send(get_random_animal_image(animal))

@random_animal.error
@lastmessage.error
@possum.error
async def on_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send('Sorry, you\'re on cooldown! Try again in `{e:.1f}` seconds.'.format(e = error.retry_after), ephemeral=True)

@DISCORD_CLIENT.event
async def on_message(message):
    ctx = await DISCORD_CLIENT.get_context(message)

    # Check to see if we're allowed to send the message first
    if (await can_message(ctx) == False):
        return
    
    # Always ignore bot messages
    if ctx.message.author.bot:
        return

    # Check for a match, if it matches, send an appropriate message
    if is_match(ctx.message):
        # Note: Unfortunately the Discord.py message object doesn't really play well with serialization or MongoDB,
        # so we have to create our own dictionary. Yuck.
        match_type = get_match_type(ctx.message)
        match_data = {"message_id": ctx.message.id, "message": ctx.message.content, "match_type": str(match_type),
            "author_id": ctx.message.author.id,
            "author": ctx.message.author.display_name, "author_username": ctx.message.author.name, 
            "created_at": ctx.message.created_at, "channel_id": message.channel.id,"guild_id": ctx.message.guild.id,
            "avatar_url": ctx.message.author.avatar.url}

        # Save basic details about the message
        num_server_match_mentions = len(list(MESSAGE_COLLECTION.find({"guild_id": bson.int64.Int64(ctx.message.guild.id),
                                                                      "match_type": str(match_type)})))
        if num_server_match_mentions > 0:
            # Find the timespan between now and the last time the match was seen in that particular Discord server, and print it out to the user
            last_match_message = MESSAGE_COLLECTION.find({"guild_id": bson.int64.Int64(ctx.message.guild.id), "match_type": str(match_type)}).sort({"created_at": -1}).limit(1).next()
            match_timespan = ctx.message.created_at - last_match_message["created_at"].replace(tzinfo=tz.tzutc()) # TODO: More elegantly handle timezones? Isn't MongoDB supposed to save this?
            timestring = format_timedelta(match_timespan)
            match_message = get_match_message(match_type, timestring)
            
            # If on cooldown, we can just send the message to the user, and not everyone.
            if CBS_COOLDOWN.get_bucket(ctx.message).update_rate_limit():
                # TODO: Find a way to send an ephemeral message since they can only be sent in response to an interaction,
                # and this flow does not count as an interaction.
                logging.warning(f"Match found, but not sent due to cooldown. Match type: {match_type}. Message: {ctx.message.content}.")
                pass
            else:             
                logging.warning(f"Match found, and sent. Match type: {match_type}. Message: {ctx.message.content}.")
                await ctx.send(match_message)
        else:
            logging.warning(f"Match found for the first time. Match type: {match_type}. Message: {ctx.message.content}.")
            init_message = get_match_initmessage(match_type)
            await ctx.send(init_message)

        # Save the data to the MongoDB database
        MESSAGE_COLLECTION.insert_one(match_data)
        logging.warning(f"Message inserted into database. Message: {ctx.message.content}.")
    
    # Process any bot commands normally using the discord.py library.
    await DISCORD_CLIENT.process_commands(ctx.message)

async def can_message(ctx):
    # The bot owner or admin should always be able to run commands
    if await ctx.bot.is_owner(ctx.author) or ctx.message.author.guild_permissions.administrator:
        return True

    # Check if we're allowed to send the message in the server
    guild_settings = SETTINGS_COLLECTION.find({"guild_id": bson.int64.Int64(ctx.message.guild.id)}).limit(1).next()
    if guild_settings["message_enabled"] == False:
        logging.warning(f"Message blocked from being sent for {ctx.message.guild.id} due to messages being disabled.")
        return False
    
    return True

@DISCORD_CLIENT.event
async def on_ready():
    logging.warning(f"CBS Bot has started.")
    await DISCORD_CLIENT.change_presence(activity=discord.Game('MAX 300 on repeat'))

@DISCORD_CLIENT.event
async def on_guild_join(self, guild: discord.Guild):
    # If we don't have an existing setting record for this guild, insert defaults
    if (has_guild_settings(guild.id) == False):
        insert_default_guild_settings(guild.id)

def has_guild_settings(guildId: int):
    number_guild_settings = len(list(SETTINGS_COLLECTION.find({"guild_id": bson.int64.Int64(guildId)})))
    return number_guild_settings > 0

def insert_default_guild_settings(guildId: int):
    default_settings = {"guild_id": guildId, "message_enabled": True}
    SETTINGS_COLLECTION.insert_one(default_settings)
    logging.warning(f"Settings did not exist for {guildId}, inserted default values.")


if __name__ == "__main__":
    DISCORD_CLIENT.run(os.environ['TOKEN'])
