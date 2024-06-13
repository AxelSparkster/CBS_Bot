from re import Match
from typing import List

import cv2
import discord
import difflib
import logging
import math
import msgspec
import os
import re
import requests
import pytesseract
import typing

from definitions import ROOT_DIR
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


pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

DEFAULT_BARCLIP = "1-15"
BARCLIP_REGEX = "(?i)(\d{1,3})-(\d{1,3})"
SONG_LIST: list[Song] = msgspec.json.decode(SONGS, type=list[Song])
LEVEL_MAP = {"novice": "NOV", "advanced": "ADV", "exhaust": "EXH", "maximum": "MXM",
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
SONG_DATA_FOLDER = ROOT_DIR + "/data/songs/sdvx"
OUTPUT_FILE_NAME = "output.png"
COLUMN_WIDTH = 254
MEASURE_GAP_TOLERANCE = 20


def map_chart_name(level_type: str) -> str:
    for word, abbreviation in LEVEL_MAP.items():
        level_type = level_type.replace(word.lower(), abbreviation)
    return level_type


def map_chart_type(level_type: str) -> str:
    for word, difficulty_abbr in LEVEL_URL_MAP.items():
        level_type = level_type.replace(word.lower(), difficulty_abbr)
    return level_type


def map_chart_url(songid: str, level_type: str) -> str:
    return f"https://sdvxindex.com/s/{songid}/{map_chart_type(level_type)}"


def map_chart_filename(songid: str, level_type: str) -> str:
    return f'{songid}-{map_chart_type(level_type)}'


def download_image_file_and_return_path(song: Song, difficulty: Difficulty) -> str:
    image = requests.get(f'https://sdvxindex.com{selected_difficulty.columnPath}').content
    path = f'{SONG_DATA_FOLDER}/{map_chart_filename(song.songid, difficulty.type)}.png'
    if not os.path.isfile(path):
        # Only save the image if it hasn't been saved.
        logging.warning(f"Cached file not found, saving file to {SONG_DATA_FOLDER}.")
        os.makedirs(SONG_DATA_FOLDER, exist_ok=True)
        with open(path, "wb") as handler:
            handler.write(image)
    else:
        logging.warning(f"Cached file already found, using file {path}.")
    return path


def get_columns_from_barclip(column_dict: dict[int, int], bar_start: str, bar_end: str):
    start_column = next((x for x in column_dict if column_dict[x] >= int(bar_start)), None)
    end_column = next((x for x in column_dict if column_dict[x] >= int(bar_end)), None)
    return start_column, end_column


def adjust_dict(column_dict: dict[int, int]) -> dict[int, int]:
    new_dict = column_dict.copy()
    for i in range(len(new_dict)):
        if i == 0:
            continue  # First value is always 1 by default, skip.
        if new_dict[i] <= new_dict[i-1] or new_dict[i] - new_dict[i-1] >= MEASURE_GAP_TOLERANCE:
            if i == 1:
                new_dict[i] = 4  # TODO: something better than this
            else:
                new_dict[i] = new_dict[i-1] + (new_dict[i-1] - new_dict[i-2])
    return new_dict


def crop_image_from_barclip(local_file_path: str, bar_start: str, bar_end: str) -> str:
    resize_value = 2
    column_width = COLUMN_WIDTH * resize_value  # Each column is about 254 pixels wide.
    roi_x1_begin = 42 * resize_value
    roi_x2_begin = 90 * resize_value
    roi_y1_begin = 35 * resize_value

    # Pre-process image for Tesseract.
    img = cv2.imread(local_file_path)
    img_rsz = cv2.resize(img, (0, 0), fx=resize_value, fy=resize_value)
    h, w, c = img_rsz.shape
    img_rct = cv2.rectangle(img_rsz, (0, h - 11 * resize_value), (w, h), (0, 0, 0), -1)
    gray_image = cv2.cvtColor(img_rct, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Get basic details about the image, so we can loop over
    # each column to check the measure numbers.
    columns = math.floor(w / column_width)

    # Loop over each ROI and get the text.
    column_dict = {0: 1}  # First column always starts with 1
    for column_num in range(1, columns):
        roi_x_1 = roi_x1_begin + (column_num * column_width)
        roi_y_1 = h - roi_y1_begin
        roi_x_2 = roi_x2_begin + (column_num * column_width)
        roi_y_2 = h
        roi = thresh[roi_y_1:roi_y_2, roi_x_1:roi_x_2]
        data = pytesseract.image_to_string(roi, lang='eng', config='--psm 10 --oem 3 -c '
                                                                   'tessedit_char_whitelist=0123456789').strip()
        measure_number = 0
        if data != "":
            measure_number = int(data)
        column_dict[column_num] = measure_number

    logging.warning(f"Column numbers: {column_dict.values()}")
    new_dict = adjust_dict(column_dict)
    logging.warning(f"Adjusted column numbers: {new_dict.values()}")
    start, end = get_columns_from_barclip(new_dict, bar_start, bar_end)
    logging.warning(f"Finished processing. Begin column should be {start} and end should be {end}.")

    h2, w2, c2 = img.shape
    crop_x_start = COLUMN_WIDTH * start
    crop_x_end = COLUMN_WIDTH * end
    crop = img[0:h2, crop_x_start:crop_x_end]
    logging.warning(f"ROI: [{crop_x_start}:{0}, {h2}:{crop_x_end}] ([x1,y1],[x2,y2]).")
    logging.warning(f"Outputting to {SONG_DATA_FOLDER}/{OUTPUT_FILE_NAME}.")
    cv2.imwrite(f"{SONG_DATA_FOLDER}/{OUTPUT_FILE_NAME}", crop)
    return f"{SONG_DATA_FOLDER}/{OUTPUT_FILE_NAME}"


class VextageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    async def song_autocomplete(self, interaction: discord.Interaction, current: str) \
            -> List[discord.app_commands.Choice[str]]:
        song_names = [x.title for x in SONG_LIST]
        close_matches = difflib.get_close_matches(current, song_names, 10, 0)
        return [
            app_commands.Choice(name=x.title(), value=x.title())
            for x in close_matches
            ]

    async def difficulty_autocomplete(self, interaction: discord.Interaction, current: str) \
            -> List[discord.app_commands.Choice[str]]:
        song_title = interaction.namespace.song
        song = next(x for x in SONG_LIST if x.title.lower() == song_title.lower())
        difficulties = [x for x in song.difficulties]
        return [
            app_commands.Choice(name=f"{map_chart_name(x.type)} {x.level}", value=str(x.level))
            for x in difficulties
            ]

    @app_commands.command(name="vextage", description="Retrieve a chart from https://sdvxindex.com/.")
    @app_commands.autocomplete(song=song_autocomplete, difficulty=difficulty_autocomplete)
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
            if len(result.groups()) != 2 or result.group(1) > result.group(2) or result is None:
                raise ValueError
            bar_clip_start = result.group(1)
            bar_clip_end = result.group(2)
        except ValueError:
            return await ctx.response.send_message("The bar clip was not formatted correctly. Make sure the "
                                                   "beginning and end values are numbers, separated by a hyphen "
                                                   "(ex: 4-23).", ephemeral=True)

        # Create the message embed
        #
        chart_url = map_chart_url(selected_song.songid, selected_difficulty.type)
        local_file_path = download_image_file_and_return_path(selected_song, selected_difficulty)
        await ctx.response.defer()
        cropped_image_path = crop_image_from_barclip(local_file_path, bar_clip_start, bar_clip_end)
        logging.warning(f"End file path: {cropped_image_path}.")
        image_file = discord.File(cropped_image_path)

        embed = discord.Embed(color=LEVEL_COLOR_MAP[selected_difficulty.type])
        embed.set_author(name=f'{selected_song.title} ({map_chart_name(selected_difficulty.type)} '
                              f'{selected_difficulty.level})')
        embed.set_thumbnail(url=f'{selected_difficulty.jacketArtPath}')
        embed.add_field(name='Song Artist', value=f'{selected_song.artist}')
        embed.add_field(name='Effected By', value=f'{selected_difficulty.effectorName}')
        embed.add_field(name='BPM', value=f'{selected_song.bpm}')
        embed.add_field(name='Illustrated By', value=f'{selected_difficulty.illustratorName}')
        embed.add_field(name='sdvxindex URL', value=f'{chart_url}',
                        inline=False)
        embed.set_image(url=f'attachment://{OUTPUT_FILE_NAME}')

        await ctx.followup.send(embed=embed, file=image_file)


def setup(bot):
    logging.warning("Vextage cog added.")
    bot.add_cog(VextageCog(bot))
