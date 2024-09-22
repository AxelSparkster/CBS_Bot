import datetime
import time
 

SECS_IN_A_DAY = 86400
SECS_IN_A_HOUR = 3600
SECS_IN_A_MIN = 60


def s(time_unit: int) -> str:
    # Decides whether the given time unit needs an "s" after its declaration
    return "s" if time_unit != 1 else ""


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

