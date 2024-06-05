import datetime
import logging
import time
from resources.models import MatchType


SECS_IN_A_DAY = 86400
SECS_IN_A_HOUR = 3600
SECS_IN_A_MIN = 60



def s(time_unit: int) -> str:
    # Decides whether the given time unit needs an "s" after its declaration
    return "s" if time_unit != 1 else ""


def get_match_term(match_type: MatchType) -> str:
    if match_type == MatchType.CBS:
        return "combo based scoring"
    elif match_type == MatchType.ROUNDONE:
        return "Round 1 being in Minnesota"
    else:
        logging.warning("Unknown match type.")


def format_timedelta(delta: datetime.timedelta) -> str:
    # Gets the number of days/hours/minutes/seconds in a user-readable string from a timedelta
    # Loosely based off of Miguendes' code here:
    # https://miguendes.me/how-to-use-datetimetimedelta-in-python-with-examples
    seconds = int(delta.total_seconds())
    days, seconds = divmod(seconds, SECS_IN_A_DAY)
    hours, seconds = divmod(seconds, SECS_IN_A_HOUR)
    minutes, seconds = divmod(seconds, SECS_IN_A_MIN)

    return f"{days} day{s(days)}, {hours} hour{s(hours)}, {minutes} minute{s(minutes)} and {seconds} second{s(seconds)}"


def convert_to_unix_time(date: datetime.datetime) -> str:
    return f'<t:{str(time.mktime(date.timetuple()))[:-2]}:R>'

