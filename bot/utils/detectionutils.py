import discord
import logging
import re
from dateutil import tz
from discord.ext import commands
from unidecode import unidecode

from bot.exts.database import get_number_match_mentions, get_last_match, insert_match_data
from bot.resources.models.enums import MatchType
from bot.utils.timeutils import format_timedelta

CBS_REGEX = "(?i)combo.*based|based.*combo"
R1_REGEX = "(?i)(round1|r1|round one|round 1).*(mn|minnesota)|(mn|minnesota).*(round1|r1|round one|round 1)"
CBS_COOLDOWN = commands.CooldownMapping.from_cooldown(2, 86400, commands.BucketType.user)
        

# TODO: Extract into a strings file, or some other method
def get_match_term(match_type: MatchType) -> str:
    if match_type == MatchType.CBS:
        return "combo based scoring"
    elif match_type == MatchType.ROUNDONE:
        return "Round 1 being in Minnesota"
    else:
        logging.warning("Unknown match type.")


def get_match_type(message: discord.Message) -> MatchType:
    # Figure out what type of match the message has
    if re.search(CBS_REGEX, unidecode(message.content)):
        return MatchType.CBS
    elif re.search(R1_REGEX, unidecode(message.content)):
        return MatchType.ROUNDONE
    else:
        return MatchType.NO_MATCH


# TODO: Extract into a strings file, or some other method
def get_match_initmessage(match_type: MatchType) -> str:
    if match_type == MatchType.CBS:
        return "Someone just mentioned combo based scoring for the first time!"
    elif match_type == MatchType.ROUNDONE:
        return "Someone just mentioned Round 1 being in Minnesota for the first time!"
    else:
        logging.warning("Unknown match type.")


# TODO: Extract into a strings file, or some other method
def get_match_message(match_type: MatchType, timestring: str) -> str:
    if match_type == MatchType.CBS:
        return f"Combo-based scoring was last mentioned {timestring} ago. The timer has been reset."
    elif match_type == MatchType.ROUNDONE:
        return f"Round 1 being in Minnesota was last mentioned {timestring} ago. The timer has been reset."
    else:
        logging.warning("Unknown match type.")


def is_match(message: discord.Message):
    # There's a match if the enum's int value is 0 or better. TODO: Is there a better way to do this?
    return int(get_match_type(message)) > 0


async def check_message_for_matches(ctx):
    # Check for a match, if it matches, send an appropriate message
    if is_match(ctx.message):
        # Note: Unfortunately the Discord.py message object doesn't really play well with serialization or MongoDB,
        # so we have to create our own dictionary. Yuck.
        match_type = get_match_type(ctx.message)
        match_data = {"message_id": ctx.message.id, "message": ctx.message.content, "match_type": str(match_type),
                      "author_id": ctx.message.author.id,
                      "author": ctx.message.author.display_name, "author_username": ctx.message.author.name,
                      "created_at": ctx.message.created_at, "channel_id": ctx.message.channel.id,
                      "guild_id": ctx.message.guild.id,
                      "avatar_url": ctx.message.author.avatar.url}

        # Save basic details about the message
        num_server_match_mentions = get_number_match_mentions(match_type, ctx.message.guild.id)
        if num_server_match_mentions > 0:
            # Find the time span between now and the last time the match was seen in that particular
            # Discord server, and print it out to the user
            last_match_message = get_last_match(match_type, ctx.message.guild.id)
            match_timespan = ctx.message.created_at - last_match_message["created_at"].replace(
                tzinfo=tz.tzutc())  # TODO: More elegantly handle timezones? Isn't MongoDB supposed to save this?
            timestring = format_timedelta(match_timespan)
            match_message = get_match_message(match_type, timestring)

            # If on cooldown, we can just send the message to the user, and not everyone.
            if CBS_COOLDOWN.get_bucket(ctx.message).update_rate_limit():
                # TODO: Find a way to send an ephemeral message since they can only be sent in response to
                #  an interaction, and this flow does not count as an interaction.
                logging.warning(
                    f"Match found, but not sent due to cooldown. Match type: {match_type}. "
                    f"Message: {ctx.message.content}.")
                pass
            else:
                logging.warning(f"Match found, and sent. Match type: {match_type}. Message: {ctx.message.content}.")
                await ctx.send(match_message)
        else:
            logging.warning(
                f"Match found for the first time. Match type: {match_type}. Message: {ctx.message.content}.")
            init_message = get_match_initmessage(match_type)
            await ctx.send(init_message)

        # Save the data to the MongoDB database
        insert_match_data(match_data)
        logging.warning(f"Message inserted into database. Message: {ctx.message.content}.")
