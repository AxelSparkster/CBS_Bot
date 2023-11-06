import discord
import re
import datetime
import os
import sys
import pandas as pd
from unidecode import unidecode

# Discord bot related junk
API_TOKEN = os.environ['TOKEN']
INTENTS = discord.Intents.default()
INTENTS.messages = True
INTENTS.message_content = True
CLIENT = discord.Client(intents=INTENTS)

# Constants
MNT_DATA_SUBDIR = "data/"
FILENAME = "cbs.csv"
CBS_REGEX = "(?i)combo.*based|based.*combo"
SECS_IN_A_DAY = 86400
SECS_IN_A_HOUR = 3600
SECS_IN_A_MIN = 60

# Necessary globals
last_cbs_mention_details = {}

def s(time_unit) -> str:
    # Decides whether or not the given time unit needs an "s" after its declaration
    return "s" if time_unit > 1 or time_unit == 0 else ""

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

def get_script_directory() -> str:
    return os.path.dirname(os.path.abspath(sys.argv[0]))

def load_previous_cbs_data():
    # Load the contents of any saved data upon bot restart
    global last_cbs_mention_details
    cbs_file = pd.read_csv(MNT_DATA_SUBDIR + FILENAME, index_col=0)
    temp_dict = cbs_file.to_dict('index')
    for val in temp_dict:
        # TODO: Find a better way to load. Only did this because dealing with a dictionary of dictionaries
        # is a pain in the ass with saving/loading and works for now
        message_id = int(temp_dict[val]["message_id"])
        message = temp_dict[val]["message"]
        author_id = int(temp_dict[val]["author_id"])
        author = temp_dict[val]["author"]
        author = temp_dict[val]["author_username"]
        date = datetime.datetime.fromisoformat(temp_dict[val]["date"])

        last_cbs_mention_details[str(val)] = {"message_id": message_id, "message": message,
        "author_id": author_id, "author": author, "date": date}

@CLIENT.event
async def on_ready():
    if os.path.isfile(MNT_DATA_SUBDIR + FILENAME):
        load_previous_cbs_data()
    await CLIENT.change_presence(activity=discord.Game('MAX 300 on repeat'))

@CLIENT.event
async def on_message(message):
    global last_cbs_mention_details

    # Always ignore bot messages
    if message.author.bot:
        return

    guild_id = message.guild.id
    # Uncomment to temporarily disable the bot from messaging the Minnesota Rhythm Gaming Discord Server
    # if guildId == 190994300354560010:
    #     return

    # Check for a match, if it matches, send an appropriate message
    if is_match(message):
        # Save basic details about the message
        this_cbs_mention = {"message_id": message.id, "message": message.content, "author_id": message.author.id,
            "author": message.author.display_name, "author_username": message.author.name, "date": datetime.datetime.now()}

        if str(guild_id) in last_cbs_mention_details:
            # If we've seen someone mention combo based scoring before, then get the last time, find the timespan between now
            # and the last time it was seen in that particular Discord server, and print it out to the user
            cbs_timespan = this_cbs_mention["date"] - last_cbs_mention_details[str(guild_id)]["date"]
            timestring = format_timedelta(cbs_timespan)
            await message.channel.send(f"It has now been {timestring} since the last time someone has mentioned combo-based scoring!")
        else:
            # If this is the first time we've seen anyone mention combo based scoring, then say an initial message
            await message.channel.send("Someone just mentioned combo based scoring for the first time!")

        # For the given Discord server, store the last time combo-based scoring was mentioned
        last_cbs_mention_details[str(guild_id)] = this_cbs_mention

        # Save the data into a csv file
        cbs_df = pd.DataFrame.from_dict(last_cbs_mention_details, orient="index")
        if os.path.isfile("./" + FILENAME):
            # TODO: Find a better way than to delete the file every single time (definitely not thread safe)
            # IDEA: Maybe periodically save every X minutes in a different method, name it different,
            # delete old file then rename it...?
            os.remove(MNT_DATA_SUBDIR + FILENAME) 
        cbs_df.to_csv(MNT_DATA_SUBDIR + FILENAME)

if __name__ == "__main__":
    CLIENT.run(API_TOKEN)