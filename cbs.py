
import bson
import datetime
import discord
import json
import logging
import os
import pymongo
import random
import re
import requests
import sys
import time
import urllib.parse
from dateutil import tz
from discord.ext import commands
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

# Constants
CBS_REGEX = "(?i)combo.*based|based.*combo"
SECS_IN_A_DAY = 86400
SECS_IN_A_HOUR = 3600
SECS_IN_A_MIN = 60

# Extra stuff
CBS_COOLDOWN = commands.CooldownMapping.from_cooldown(2, 86400, commands.BucketType.user)

def s(time_unit) -> str:
    # Decides whether or not the given time unit needs an "s" after its declaration
    return "s" if time_unit != 1 else ""

def is_match(message):
    # Returns true if the words "combo" and "based" show up (this can be VERY heavily improved lmao)
    return re.search(CBS_REGEX, unidecode(message.content))

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

# Gets URL of random animal image.
# Valid inputs (we can autocomplete this later via slash commands):
#
# ["fox", "yeen", "dog", "manul", "snek", "poss", "leo", "serval", "bleat",
# "shiba", "racc", "dook", "ott", "snep", "woof", "chi", "capy", "bear", "bun",
# "caracal", "puma", "mane", "marten", "tig", "wah", "skunk", "jaguar", "yote"]
def get_random_animal_image(animal: str) -> str:
    params = {'animal': animal}
    response = requests.get("https://api.tinyfox.dev/img.json", params)
    animal_url = "https://api.tinyfox.dev" + response.json().get("loc")
    return animal_url

@DISCORD_CLIENT.hybrid_command(name="sync", description="(Owner/Admin only) Syncs the command tree.")
async def sync(ctx) -> None:
    if await ctx.bot.is_owner(ctx.author) or await ctx.message.author.guild_permissions.administrator:
        await DISCORD_CLIENT.tree.sync()
        logging.warning("Command tree synced.")
        await ctx.message.channel.send("Command tree synced.")

@DISCORD_CLIENT.hybrid_command(name="shutup", description="(Owner/Admin only) Disables the bot from messaging in the server.")
async def shutup(ctx) -> None:
    if await ctx.bot.is_owner(ctx.author) or await ctx.message.author.guild_permissions.administrator:
        logging.warning(f"Disabling messages for guild ID {ctx.message.guild.id}.")
        SETTINGS_COLLECTION.update_one({"guild_id": bson.int64.Int64(ctx.message.guild.id)}, {"$set": { "message_enabled": False }})
        await ctx.message.channel.send("Messages have been disabled.")

@DISCORD_CLIENT.hybrid_command(name="getupanddanceman", description="(Owner/Admin only) Reenables the bot's ability to message in the server.")
async def getupanddanceman(ctx) -> None:
    if await ctx.bot.is_owner(ctx.author) or await ctx.message.author.guild_permissions.administrator:
        logging.warning(f"Enabling messages for guild ID {ctx.message.guild.id}.")
        SETTINGS_COLLECTION.update_one({"guild_id": bson.int64.Int64(ctx.message.guild.id)}, {"$set": { "message_enabled": True }})
        await ctx.message.channel.send("Messages have been enabled.")

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
    await ctx.message.channel.send(get_random_animal_image("poss"))

@DISCORD_CLIENT.event
async def on_message(message):
    ctx = await DISCORD_CLIENT.get_context(message)

    # Always ignore bot messages
    if message.author.bot:
        return

    # Check for a match, if it matches, send an appropriate message
    if is_match(message):
        # Save basic details about the message
        num_server_cbs_mentions = len(list(MESSAGE_COLLECTION.find({"guild_id": bson.int64.Int64(message.guild.id)})))
        if num_server_cbs_mentions > 0:
            # Prevent people from spamming "combo based" via global cooldown - We'll just return and have the bot send nothing.
            if CBS_COOLDOWN.get_bucket(message).update_rate_limit(): return
            
            # If we've seen someone mention combo based scoring before, then get the last time, find the timespan between now
            # and the last time it was seen in that particular Discord server, and print it out to the user
            last_cbs_message = MESSAGE_COLLECTION.find({"guild_id": bson.int64.Int64(message.guild.id)}).sort({"created_at": -1}).limit(1).next()
            cbs_timespan = message.created_at - last_cbs_message["created_at"].replace(tzinfo=tz.tzutc()) # TODO: More elegantly handle timezones? Isn't MongoDB supposed to save this?
            timestring = format_timedelta(cbs_timespan)
            if (can_message(ctx) == False): return
            await message.channel.send(f"Combo-based scoring was last mentioned {timestring} ago. The timer has been reset.")
        else:
            # If this is the first time we've seen anyone mention combo based scoring, then say an initial message
            if (can_message(ctx) == False): return
            await message.channel.send("Someone just mentioned combo based scoring for the first time!")

        # Save the data to the MongoDB database
        #
        # Note: Unfortunately the Discord.py message object doesn't really play well with serialization or MongoDB,
        # so we have to create our own dictionary. Yuck.
        # TODO: Bring this further up and record it earlier in this logic.
        data = {"message_id": message.id, "message": message.content, "author_id": message.author.id,
            "author": message.author.display_name, "author_username": message.author.name, 
            "created_at": message.created_at, "channel_id": message.channel.id,"guild_id": message.guild.id,
            "avatar_url": message.author.avatar.url}
        MESSAGE_COLLECTION.insert_one(data)

    # Check to see if we're allowed to send the message first
    # TODO: Make this one of the first checks, bypassable as bot owner or admin
    if (can_message(ctx) == False):
        return
    
    # Process any bot commands normally using the discord.py library.
    await DISCORD_CLIENT.process_commands(message)

@DISCORD_CLIENT.event
async def on_ready():
    logging.warning(f"CBS Bot has started.")
    await DISCORD_CLIENT.change_presence(activity=discord.Game('MAX 300 on repeat'))

def can_message(ctx):
    if(ctx.command is not None and (ctx.command.name == "getupanddanceman" or ctx.command.name == "shutup")):
        logging.warning(f"Message enable/disable command detected, bypassing message checks.")
        return True

    # If we don't have an existing setting record for this guild, insert defaults
    if (has_guild_settings(ctx.message) == False):
        default_settings = {"guild_id": ctx.message.guild.id, "message_enabled": True, "max_possums_per_day": 5, 
                    "max_cbs_uses_per_day": 5}
        SETTINGS_COLLECTION.insert_one(default_settings)
        logging.warning(f"Settings did not exist for {ctx.message.guild.id}, inserted default values.")

    # Check if we're allowed to send the message in the server
    guild_settings = SETTINGS_COLLECTION.find({"guild_id": bson.int64.Int64(ctx.message.guild.id)}).limit(1).next()
    if guild_settings["message_enabled"] == False:
        logging.warning(f"Message blocked from being sent for {ctx.message.guild.id} due to messages being disabled.")
        return False
    
    return True

def has_guild_settings(message):
    number_guild_settings = len(list(SETTINGS_COLLECTION.find({"guild_id": bson.int64.Int64(message.guild.id)})))
    return number_guild_settings > 0

if __name__ == "__main__":
    DISCORD_CLIENT.run(os.environ['TOKEN'])
