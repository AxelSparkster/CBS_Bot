from typing import List

import msgspec
import logging
import discord
import difflib
import typing

from discord import app_commands
from discord.ext import commands
from bot.resources.models import DifficultyEnum
from bot.resources.songdata import SONGS
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


SONG_LIST: list[Song] = msgspec.json.decode(SONGS, type=list[Song])
LEVEL_MAP = {"novice": "NOV", "advanced": "ADV", "exhaust": "NOV", "maximum": "MXM",
             "infinite": "INF", "gravity": "GRV", "heavenly": "HVN", "vivid": "VVD", "exceed": "XCD"}


def map_level_name(level_type: str) -> str:
    for word, abbreviation in LEVEL_MAP.items():
        level_type = level_type.replace(word.lower(), abbreviation)
    return level_type


class VextageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    async def song_auto(self, interaction: discord.Interaction, current: str) \
            -> List[discord.app_commands.Choice[str]]:
        song_names = [x.title for x in SONG_LIST]
        close_matches = difflib.get_close_matches(current, song_names, 10, 0)
        return [
            app_commands.Choice(name=x.title(), value=x.title())
            for x in close_matches
            ]

    async def difficulty_auto(self, interaction: discord.Interaction, current: str) \
            -> List[discord.app_commands.Choice[str]]:
        song_title = interaction.namespace.song
        song = next(x for x in SONG_LIST if x.title.lower() == song_title.lower())
        difficulties = [x for x in song.difficulties]
        return [
            app_commands.Choice(name=f"{map_level_name(x.type)} {x.level}", value=str(x.level))
            for x in difficulties
            ]

    @app_commands.command(name="vextage", description="Retrieve a chart from https://sdvxindex.com/.")
    @app_commands.autocomplete(song=song_auto, difficulty=difficulty_auto)
    async def vextage(self, ctx, song: str, difficulty: str, bar_clip: typing.Optional[str]) -> None:
        global selected_song
        global level

        logging.warning(f"Song list loaded. Looking for song: \"{song}\"")

        try:
            selected_song = next(x for x in SONG_LIST if x.title.lower() == song.lower())
        except StopIteration:
            return await ctx.response.send_message("Not really sure what song that is. Try using the "
                                                   "autocomplete function and don't edit the results!", ephemeral=True)
        logging.warning(f"Difficulties: {[x.level for x in selected_song.difficulties]}")
        try:
            level = int(difficulty)
            if level not in [x.level for x in selected_song.difficulties]:
                raise ValueError
        except ValueError:
            return await ctx.response.send_message("Not really sure what difficulty that is. Try using the "
                                                   "autocomplete function and don't edit the results!", ephemeral=True)

        logging.warning(f"Song identified: {selected_song.title}. Difficulty identified: {difficulty}. "
                        f"Bar clip: {bar_clip}.")
        await ctx.response.send_message(f'You just looked for the song {selected_song.title}. It was made by '
                                        f'{selected_song.artist}, released on {selected_song.date}, and has '
                                        f'difficulties of {[x.level for x in selected_song.difficulties]}.')


def setup(bot):
    logging.warning("Vextage cog added.")
    bot.add_cog(VextageCog(bot))
