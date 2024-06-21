import discord
from msgspec import Struct


class Radar(Struct, kw_only=True):
    notes: int = 0
    peak: int = 0
    tsumami: int = 0
    tricky: int = 0
    handtrip: int = 0
    onehand: int = 0


class Difficulty(Struct, kw_only=True):
    level: int = 0
    type: str = ""
    imagePath: str = ""
    columnPath: str = ""
    effectorName: str = ""
    illustratorName: str = ""
    max_exscore: str = ""
    radar: Radar = None
    jacketArtPath: str = ""


class Song(Struct, kw_only=True):
    songid: str = ""
    title: str = ""
    artist: str = ""
    ascii: str = ""
    title_yomigana: str = ""
    artist_yomigana: str = ""
    version: str = ""
    bpm: str = ""
    genres: list[str] = list[""]
    date: str = ""
    difficulties: list[Difficulty] = None


class DifficultyPlus(Struct, kw_only=True):
    idx: int = 0
    effector: str = ""
    level: int = 0
    name: str = ""
    jacketPath: str = ""


class SongPlus(Struct, kw_only=True):
    diffs: list[DifficultyPlus] = None
    id: int = 0
    title: str = ""
    artist: str = ""
    dateAdded: int = 0


LEVEL_MAPPINGS = {"novice": {"shorthand": "NOV", "url_mapping": "1",
                             "color": discord.Color.from_rgb(145, 75, 198)},
                  "advanced": {"shorthand": "ADV", "url_mapping": "2",
                               "color": discord.Color.from_rgb(168, 163, 7)},
                  "exhaust": {"shorthand": "EXH", "url_mapping": "3",
                              "color": discord.Color.from_rgb(148, 52, 52)},
                  "maximum": {"shorthand": "MXM", "url_mapping": "5",
                              "color": discord.Color.from_rgb(112, 112, 112)},
                  "infinite": {"shorthand": "INF", "url_mapping": "4i",
                               "color": discord.Color.from_rgb(179, 37, 101)},
                  "gravity": {"shorthand": "GRV", "url_mapping": "4g",
                              "color": discord.Color.from_rgb(158, 66, 0)},
                  "heavenly": {"shorthand": "HVN", "url_mapping": "4h",
                               "color": discord.Color.from_rgb(0, 127, 166)},
                  "vivid": {"shorthand": "VVD", "url_mapping": "4v",
                            "color": discord.Color.from_rgb(184, 68, 155)},
                  "exceed": {"shorthand": "XCD", "url_mapping": "4x",
                             "color": discord.Color.from_rgb(54, 81, 145)}}
