from re import Match
from typing import List

import msgspec
import logging
import discord
import difflib
import typing
import re

from discord import app_commands
from discord.ext import commands
from bot.resources.songdata import SONGS
from msgspec import Struct
from unidecode import unidecode


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


DEFAULT_BARCLIP = "1-15"
BARCLIP_REGEX = "(?i)(\d{1,3})-(\d{1,3})"
SONG_LIST: list[Song] = msgspec.json.decode(SONGS, type=list[Song])
LEVEL_MAP = {"novice": "NOV", "advanced": "ADV", "exhaust": "NOV", "maximum": "MXM",
             "infinite": "INF", "gravity": "GRV", "heavenly": "HVN", "vivid": "VVD", "exceed": "XCD"}
LEVEL_URL_MAP = {"novice": "1", "advanced": "2", "exhaust": "3", "maximum": "5",
             "infinite": "4i", "gravity": "4g", "heavenly": "4h", "vivid": "4v", "exceed": "4x"}
LEVEL_COLOR_MAP = {"novice": discord.Color.from_rgb(145, 75, 198),
                   "advanced": discord.Color.from_rgb(168, 163, 7),
                   "exhaust": discord.Color.from_rgb(148, 52, 52),
                   "maximum": discord.Color.from_rgb(112, 112, 112),
                   "infinite": discord.Color.from_rgb(179, 37, 101),
                   "gravity": discord.Color.from_rgb(158, 66, 0),
                   "heavenly": discord.Color.from_rgb(0, 127, 166),
                   "vivid": discord.Color.from_rgb(184, 68, 155),
                   "exceed": discord.Color.from_rgb(54, 81, 145)}


def map_level_name(level_type: str) -> str:
    for word, abbreviation in LEVEL_MAP.items():
        level_type = level_type.replace(word.lower(), abbreviation)
    return level_type


def map_level_url(songid: str, level_type: str) -> str:
    for word, difficulty_abbr in LEVEL_URL_MAP.items():
        level_type = level_type.replace(word.lower(), difficulty_abbr)
    return f"https://sdvxindex.com/s/{songid}/{level_type}"


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
        global selected_difficulty
        global bar_clip_start
        global bar_clip_end

        logging.warning(f"Song list loaded. Looking for song: \"{song}\"")

        try:
            selected_song = next(x for x in SONG_LIST if x.title.lower() == song.lower())
        except StopIteration:
            return await ctx.response.send_message("Not really sure what song that is. Try using the "
                                                   "autocomplete function and don't edit the results!", ephemeral=True)

        try:
            level = int(difficulty)
            if level not in [x.level for x in selected_song.difficulties]:
                raise ValueError
            selected_difficulty = next(x for x in selected_song.difficulties if x.level == level)
        except ValueError:
            return await ctx.response.send_message("Not really sure what difficulty that is. Try using the "
                                                   "autocomplete function and don't edit the results!", ephemeral=True)

        try:
            if bar_clip is None:
                bar_clip = DEFAULT_BARCLIP
            result = re.search(BARCLIP_REGEX, unidecode(bar_clip))
            logging.warning(f"Group length: {len(result.groups())}. Values: {result.group(1)} {result.group(2)}")
            if len(result.groups()) != 2 or result.group(1) > result.group(2) or result is None:
                raise ValueError
            bar_clip_start = result.group(1)
            bar_clip_end = result.group(2)
        except ValueError:
            return await ctx.response.send_message("The bar clip was not formatted correctly. Make sure the "
                                                   "beginning and end values are numbers, separated by a hyphen "
                                                   "(ex: 4-23).", ephemeral=True)

        # logging.warning(f"Song identified: {selected_song.title}. Difficulty identified: {difficulty}. "
        #                 f"Bar clip: {bar_clip}.")
        # await ctx.response.send_message(f'You just looked for the song {selected_song.title}. It was made by '
        #                                 f'{selected_song.artist}, released on {selected_song.date}, and has '
        #                                 f'difficulties of {[x.level for x in selected_song.difficulties]}.')

        # Create the message embed
        #
        embed = discord.Embed(color=LEVEL_COLOR_MAP[selected_difficulty.type])
        embed.set_author(name=f'{selected_song.title} ({map_level_name(selected_difficulty.type)} '
                              f'{selected_difficulty.level})')
        embed.set_thumbnail(url=f'{selected_difficulty.jacketArtPath}')
        embed.add_field(name='Song Artist', value=f'{selected_song.artist}')
        embed.add_field(name='Effected By', value=f'{selected_difficulty.effectorName}')
        embed.add_field(name='BPM', value=f'{selected_song.bpm}')
        embed.add_field(name='Illustrated By', value=f'{selected_difficulty.illustratorName}')
        embed.add_field(name='sdvxindex URL', value=f'{map_level_url(selected_song.songid, selected_difficulty.type)}',
                        inline=False)
        embed.set_footer(text="Note: This message is sent silently and does not ping users.")
        embed.set_image(url=f'https://sdvxindex.com{selected_difficulty.columnPath}')

        await ctx.response.send_message(embed=embed, silent=True)


def setup(bot):
    logging.warning("Vextage cog added.")
    bot.add_cog(VextageCog(bot))
