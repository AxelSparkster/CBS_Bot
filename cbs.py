import discord
import re
import datetime
from unidecode import unidecode

# Discord bot related junk
API_TOKEN = '<INSERT TOKEN HERE>'
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# Constants
CBS_REGEX = "(?i)combo.*based|based.*combo"
SECS_IN_A_DAY = 86400
SECS_IN_A_HOUR = 3600
SECS_IN_A_MIN = 60

# Necessary globals
last_cbs_mention = {}

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

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('MAX 300 on repeat'))

@client.event
async def on_message(message):
    global last_cbs_mention

    # Always ignore the bot's messages
    if message.author.bot:
        return

    guild_id = message.guild.id
    # Uncomment to temporarily disable the bot from messaging the Minnesota Rhythm Gaming Discord Server
    # if guildId == 190994300354560010:
    #     return

    # Check for a match, if it matches, send an appropriate message
    if is_match(message):
        this_cbs_mention = datetime.datetime.now()
        if str(guild_id) in last_cbs_mention:
            # If we've seen someone mention combo based scoring before, then get the last time, find the timespan between now
            # and the last time it was seen in that particular Discord server, and print it out to the user
            cbs_timespan = this_cbs_mention - last_cbs_mention[str(guild_id)]
            timestring = format_timedelta(cbs_timespan)
            await message.channel.send(f"It has now been {timestring} since the last time someone has mentioned combo-based scoring!")
        else:
            # If this is the first time we've seen anyone mention combo based scoring, then say an initial message
            last_cbs_mention[str(guild_id)] = this_cbs_mention
            await message.channel.send("Someone just mentioned combo based scoring for the first time!")

        # For the given Discord server, store the last time combo-based scoring was mentioned
        last_cbs_mention[str(guild_id)] = this_cbs_mention

if __name__ == "__main__":
    client.run(API_TOKEN)