import discord
from typing import Literal


ANIMAL_LITERAL = Literal["fox", "yeen", "dog", "manul", "snek", "poss", "serval", "bleat",
                         "shiba", "racc", "dook", "ott", "snep", "woof", "capy", "bear", "bun",
                         "caracal", "puma", "mane", "marten", "wah", "skunk", "jaguar", "yote"]

RATING_MAPPINGS = {"SSS+": {"color": discord.Color.from_rgb(255, 255, 255)},
                  "SSS": {"color": discord.Color.from_rgb(204, 0, 102)},
                  "SS+": {"color": discord.Color.from_rgb(204, 0, 0)},
                  "SS": {"color": discord.Color.from_rgb(255, 51, 0)},
                  "S+": {"color": discord.Color.from_rgb(255, 153, 51)},
                  "S": {"color": discord.Color.from_rgb(255, 153, 102)},
                  "A": {"color": discord.Color.from_rgb(153, 0, 255)},
                  "B": {"color": discord.Color.from_rgb(51, 51, 255)},
                  "C": {"color": discord.Color.from_rgb(102, 255, 51)},
                  "D": {"color": discord.Color.from_rgb(166, 166, 166)}}
