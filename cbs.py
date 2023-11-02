import discord
import re
import datetime

# Discord bot related junk
API_TOKEN = '<INSERT TOKEN HERE>'
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# Necessary globals
CBS_REGEX = "(?i)combo.*based|based.*combo"
last_cbs_mention = {}

def is_match(message):
    # Returns true if the words "combo" and "based" show up (this can be VERY heavily improved lmao)
    return re.search(CBS_REGEX, message.content)

def format_timedelta(delta: datetime.timedelta) -> str:
    # Gets the number of days/hours/minutes/seconds in a user-readable string from a timedelta.
    # Loosely based off of Miguendes' code here: https://miguendes.me/how-to-use-datetimetimedelta-in-python-with-examples

    seconds = int(delta.total_seconds())

    secs_in_a_day = 86400
    secs_in_a_hour = 3600
    secs_in_a_min = 60

    days, seconds = divmod(seconds, secs_in_a_day)
    hours, seconds = divmod(seconds, secs_in_a_hour)
    minutes, seconds = divmod(seconds, secs_in_a_min)

    # Check if anything needs suffixes.
    d_sx = "s" if days > 1 or days == 0 else ""
    h_sx = "s" if hours > 1 or days == 0 else ""
    m_sx = "s" if minutes > 1 or days == 0 else ""
    s_sx = "s" if seconds > 1 or days == 0 else ""

    return f"{days} day{d_sx}, {hours} hour{h_sx}, {minutes} minute{m_sx} and {seconds} second{s_sx}"

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('MAX 300 on repeat'))

@client.event
async def on_message(message):
    global last_cbs_mention

    # Always ignore the bot's messages
    if message.author.bot:
        return
    # Uncomment to temporarily disable the bot from messaging the MN Rhythm Gaming discord.
    # if guildId == 190994300354560010:
    #     return

    # Check for a match, if it matches, send an appropriate message
    guildId = message.guild.id
    if is_match(message):
        this_cbs_mention = datetime.datetime.now()
        if str(guildId) in last_cbs_mention:
            # If we've seen someone mention combo based scoring before, then get the last time, find the timespan between now
            # and the last time it was seen in that particular Discord server, and print it out to the user.
            cbs_timespan = this_cbs_mention - last_cbs_mention[str(guildId)]
            timestring = format_timedelta(cbs_timespan)
            await message.channel.send(f"It has now been {timestring} since the last time someone has mentioned combo-based scoring!")
        else:
            # If this is the first time we've seen anyone mention combo based scoring, then say an initial message.
            last_cbs_mention[str(guildId)] = this_cbs_mention
            await message.channel.send("Someone just mentioned combo based scoring for the first time!")

        # For the given Discord server, store the last time combo-based scoring was mentioned.
        last_cbs_mention[str(guildId)] = this_cbs_mention

if __name__ == "__main__":
    client.run(API_TOKEN)