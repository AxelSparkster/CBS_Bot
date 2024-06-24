import discord
from msgspec import Struct


class DdrSong(Struct, kw_only=True):
    song_id: str = ""
    song_name: str = ""
    searchable_name: str = ""
    romanized_name: str = ""
    alternate_name: str = ""
    alphabet: str = ""
    version_num: int = 0
    ratings: list[int] = list[0]
    tiers: list[float] = list[0]


LEVEL_MAPPINGS = {"beginner": {"color": discord.Color.from_rgb(64, 198, 233)},
                  "basic": {"color": discord.Color.from_rgb(235, 210, 45)},
                  "difficult": {"color": discord.Color.from_rgb(234, 24, 25)},
                  "expert": {"color": discord.Color.from_rgb(41, 232, 35)},
                  "challenge": {"color": discord.Color.from_rgb(190, 36, 220)}}

VERSION_MAPPINGS = {1: "DDR 1st",
                    2: "DDR 2nd",
                    3: "DDR 3rd",
                    4: "DDR 4th",
                    5: "DDR 5th",
                    6: "DDR MAX",
                    7: "DDR MAX2",
                    8: "DDR Extreme",
                    9: "DDR SuperNOVA",
                    10: "DDR SuperNOVA2",
                    11: "DDR X",
                    12: "DDR X2",
                    13: "DDR X3 vs 2nd",
                    14: "DDR 2013",
                    15: "DDR 2014",
                    16: "A",
                    17: "A20",
                    18: "A20 Plus",
                    19: "A3",
                    20: "WORLD"}
