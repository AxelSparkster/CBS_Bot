
import bson
import datetime
import discord
import json
import logging
import os
import pymongo
import random
import re
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

# Constants
CBS_REGEX = "(?i)combo.*based|based.*combo"
SECS_IN_A_DAY = 86400
SECS_IN_A_HOUR = 3600
SECS_IN_A_MIN = 60

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

@DISCORD_CLIENT.command()
async def lastmessage(ctx):
    # Gets details of last message
    last_cbs_message = MESSAGE_COLLECTION.find({"guild_id": bson.int64.Int64(ctx.message.guild.id)}).sort({"created_at": -1}).limit(1).next()
    last_cbs_message_link = f'https://canary.discord.com/channels/{last_cbs_message["guild_id"]}/{last_cbs_message["channel_id"]}/{last_cbs_message["message_id"]}'
    preface_message = (f'The last mention of combo-based scoring was {convert_to_unix_time(last_cbs_message["created_at"])} by '
                       f'<@{last_cbs_message["author_id"]}>, which was here: {last_cbs_message_link}\n\n')
    localized_date = last_cbs_message["created_at"].replace(tzinfo=tz.gettz('UTC')).astimezone(tz.gettz('America/Chicago'))

    embed = discord.Embed(color=discord.Color.red())
    embed.set_author(name=f'{last_cbs_message["author"]}', icon_url=f'{last_cbs_message["avatar_url"]}')
    embed.add_field(name='Message', value=f'{last_cbs_message["message"]}', inline=False)
    embed.add_field(name='Date', value=f'{localized_date.strftime("%B %d, %Y %I:%M %p %Z%z")}', inline=False)
    embed.set_footer(text="Note: This message is sent silently and does not ping users.")

    await ctx.send(content=f'{preface_message}', embed=embed, silent=True)


@DISCORD_CLIENT.command()
async def possum(ctx):
    # Gets random possum image :)
    random_possum_word = random.choice(["sitting", "standing", "scream", "confused", "baby", "rolling", "dumb", "cute", "cool", "meme"])
    request = urllib.request.Request(f'https://www.googleapis.com/customsearch/v1?key={os.getenv("GIS_API_KEY")}' +
        f'&cx={os.getenv("GIS_PROJECT_CX")}&q=opossum%20{random_possum_word}&searchType=image')
    with urllib.request.urlopen(request) as f:
        data = f.read().decode('utf-8')
    await ctx.message.channel.send(random.choice(json.loads(data)['items'])['link'])

@DISCORD_CLIENT.event
async def on_message(message):

    # Always ignore bot messages
    if message.author.bot:
        return

    # Edit the .env file to allow/disallow the bot from running in the MNRG server:
    mnrg_disabled = os.getenv("MNRG_DISABLE", 'True').lower() in ('true', '1', 't')
    if message.guild.id == 190994300354560010 and mnrg_disabled:
        return

    # Check for a match, if it matches, send an appropriate message
    if is_match(message):
        # Save basic details about the message
        num_server_cbs_mentions = len(list(MESSAGE_COLLECTION.find({"guild_id": bson.int64.Int64(message.guild.id)})))
        if num_server_cbs_mentions > 0:
            # If we've seen someone mention combo based scoring before, then get the last time, find the timespan between now
            # and the last time it was seen in that particular Discord server, and print it out to the user
            last_cbs_message = MESSAGE_COLLECTION.find({"guild_id": bson.int64.Int64(message.guild.id)}).sort({"created_at": -1}).limit(1).next()
            cbs_timespan = message.created_at - last_cbs_message["created_at"].replace(tzinfo=tz.tzutc()) # TODO: More elegantly handle timezones? Isn't MongoDB supposed to save this?
            timestring = format_timedelta(cbs_timespan)
            await message.channel.send(f"It has now been {timestring} since the last time someone has mentioned combo-based scoring!")
        else:
            # If this is the first time we've seen anyone mention combo based scoring, then say an initial message
            await message.channel.send("Someone just mentioned combo based scoring for the first time!")

        # Save the data to the MongoDB database
        #
        # Note: Unfortunately the Discord.py message object doesn't really play well with serialization or MongoDB,
        # so we have to create our own dictionary. Yuck.
        data = {"message_id": message.id, "message": message.content, "author_id": message.author.id,
            "author": message.author.display_name, "author_username": message.author.name, 
            "created_at": message.created_at, "channel_id": message.channel.id,"guild_id": message.guild.id,
            "avatar_url": message.author.avatar.url}
        MESSAGE_COLLECTION.insert_one(data)
    
    # Process any bot commands normally using the discord.py library.
    await DISCORD_CLIENT.process_commands(message)

@DISCORD_CLIENT.event
async def on_ready():
    await DISCORD_CLIENT.change_presence(activity=discord.Game('MAX 300 on repeat'))

if __name__ == "__main__":
    DISCORD_CLIENT.run(os.environ['TOKEN'])
