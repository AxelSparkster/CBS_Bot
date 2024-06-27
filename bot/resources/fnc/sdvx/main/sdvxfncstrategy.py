import json
import discord
import logging
import msgspec
import os
import requests
import re
from discord import Embed
from unidecode import unidecode

from bot.resources.fnc.fncstrategy import FncStrategy
from bot.resources.fnc.sdvx.main.songdata import SONGS
from bot.resources.fnc.sdvx.sdvxfncmodels import Song, LEVEL_MAPPINGS
from bot.resources.fnc.fncconstants import DEFAULT_BARCLIP, BARCLIP_REGEX, SONG_DATA_FOLDER, OUTPUT_FILE_NAME

SONG_LIST: list[Song] = msgspec.json.decode(SONGS, type=list[Song])


class SdvxFncStrategy(FncStrategy):
    def __init__(self, x1_left_px, x2_left_px, y1_bottom_px, y2_bottom_px, spacing_px, doubles_spacing_px,
                 bottom_cutoff_px, ocr_scale_multiplier, measure_oob_tol, game_title):
        super(SdvxFncStrategy, self).__init__(x1_left_px, x2_left_px, y1_bottom_px, y2_bottom_px, spacing_px,
                                              doubles_spacing_px, bottom_cutoff_px, ocr_scale_multiplier,
                                              measure_oob_tol, game_title)
        pass

    async def execute_strategy(self, ctx, **kwargs):
        await super(SdvxFncStrategy, self).execute_strategy(ctx, **kwargs)

    async def map_chart_name(self, **kwargs) -> str:
        level_type = kwargs["level_type"]

        for word, info in LEVEL_MAPPINGS.items():
            level_type = level_type.replace(word.lower(), info["shorthand"])
        return level_type

    async def get_barclip(self, bar_clip: str):
        return await super(SdvxFncStrategy, self).get_barclip(bar_clip)

    async def map_chart_type(self, **kwargs) -> str:
        level_type = kwargs["level_type"]

        for word, info in LEVEL_MAPPINGS.items():
            level_type = level_type.replace(word.lower(), info["url_mapping"])
        return level_type

    async def map_chart_filename(self, **kwargs) -> str:
        return f"{kwargs['song'].songid}-{await self.map_chart_type(level_type=kwargs['difficulty'].type)}"

    async def download_image_file(self, **kwargs) -> str:
        song = kwargs["song"]
        difficulty = kwargs["difficulty"]

        image = requests.get(f'https://sdvxindex.com{difficulty.columnPath}').content
        filename = await self.get_local_song_id_folder_plus_filename(song=song, difficulty=difficulty)
        if not os.path.isfile(filename):
            # Cache the file if it doesn't exist.
            path = await self.get_local_song_id_folder(song=song)
            os.makedirs(path, exist_ok=True)
            with open(filename, "wb") as handler:
                handler.write(image)
        else:
            logging.warning(f"Cached file already found, using file {filename}.")
        return filename

    async def use_doubles_spacing(self, **kwargs):
        return await super(SdvxFncStrategy, self).use_doubles_spacing(**kwargs)

    async def get_measure_numbers_from_image(self, file_path: str, use_doubles_spacing: bool) -> dict[int, int]:
        return await super(SdvxFncStrategy, self).get_measure_numbers_from_image(file_path, use_doubles_spacing)

    async def adjust_measures(self, column_dict: dict[int, int]) -> dict[int, int]:
        return await super(SdvxFncStrategy, self).adjust_measures(column_dict)

    async def get_columns_from_barclip(self, column_dict: dict[int, int], bar_start: str, bar_end: str):
        return await super(SdvxFncStrategy, self).get_columns_from_barclip(column_dict, bar_start, bar_end)

    async def sanitize_inputs(self, ctx, **kwargs):
        try:
            selected_song = next(x for x in SONG_LIST if x.title.lower() == kwargs["song"].lower())
        except StopIteration:
            return await ctx.response.send_message("Not really sure what song that is. Try using the "
                                                   "autocomplete function and don't edit the results!", ephemeral=True)

        try:
            if int(kwargs["difficulty"]) not in [x.level for x in selected_song.difficulties]:
                raise ValueError
        except ValueError:
            return await ctx.response.send_message("Not really sure what difficulty that is. Try using the "
                                                   "autocomplete function and don't edit the results!", ephemeral=True)

        try:
            bar_clip = kwargs["bar_clip"]
            if bar_clip is None:
                bar_clip = DEFAULT_BARCLIP
            result = re.search(BARCLIP_REGEX, unidecode(bar_clip))
            if len(result.groups()) != 2 or result.group(1) > result.group(2) or result is None:
                raise ValueError
        except ValueError:
            return await ctx.response.send_message("The bar clip was not formatted correctly. Make sure the "
                                                   "beginning and end values are numbers, separated by a hyphen "
                                                   "(ex: 4-23).", ephemeral=True)
        pass

    async def get_song_url(self, **kwargs) -> str:
        return (f"https://sdvxindex.com/s/{kwargs['song'].songid}/"
                f"{await self.map_chart_type(level_type=kwargs['difficulty'].type)}")

    async def crop_image(self, local_file_path: str, start_column: int, end_column: int,
                         use_doubles_spacing: bool) -> str:
        return await super(SdvxFncStrategy, self).crop_image(local_file_path, start_column, end_column,
                                                             use_doubles_spacing)

    async def create_embed(self, cropped_image_path: str, chart_url: str, **kwargs) -> Embed:
        song = kwargs["song"]
        difficulty = kwargs["difficulty"]

        embed = discord.Embed(color=LEVEL_MAPPINGS[difficulty.type]["color"])
        embed.set_author(name=f'{song.title} ({await self.map_chart_name(level_type=difficulty.type)} '
                              f'{difficulty.level})')
        embed.set_thumbnail(url=f'{difficulty.jacketArtPath}')
        embed.add_field(name='Song Artist', value=f'{song.artist}')
        embed.add_field(name='Effected By', value=f'{difficulty.effectorName}')
        embed.add_field(name='BPM', value=f'{song.bpm}')
        embed.add_field(name='Illustrated By', value=f'{difficulty.illustratorName}')
        embed.add_field(name='sdvxindex URL', value=f'{chart_url}',
                        inline=False)
        embed.set_image(url=f'attachment://{OUTPUT_FILE_NAME}')
        return embed

    async def get_measure_file_name(self, **kwargs):
        partial_filename = await self.map_chart_filename(song=kwargs["song"], difficulty=kwargs["difficulty"])
        return f"measures-{partial_filename}.json"

    async def measure_file_exists(self, **kwargs) -> bool:
        song = kwargs["song"]
        difficulty = kwargs["difficulty"]

        filename = await self.get_measure_file_name(song=song, difficulty=difficulty)
        path = await self.get_local_song_id_folder(song=song)
        return os.path.isfile(f"{path}{filename}")

    async def get_measure_numbers_from_file(self, **kwargs) -> dict[int, int]:
        song = kwargs["song"]

        filename = await self.get_measure_file_name(song=song, difficulty=kwargs["difficulty"])
        path = await self.get_local_song_id_folder(song=song)
        with open(f"{path}{filename}") as fp:
            data = json.load(fp)
        return {int(key): value for key, value in data.items()}

    async def save_measure_numbers_to_file(self, measures: dict[int, int], **kwargs):
        song = kwargs["song"]
        difficulty = kwargs["difficulty"]

        filename = await self.get_measure_file_name(song=song, difficulty=difficulty)
        path = await self.get_local_song_id_folder(song=song)
        os.makedirs(path, exist_ok=True)
        with open(f"{path}{filename}", 'w') as fp:
            json.dump(measures, fp)

    async def get_local_song_id_folder_plus_filename(self, **kwargs) -> str:
        filename = await self.map_chart_filename(song=kwargs['song'], difficulty=kwargs["difficulty"])
        path = await self.get_local_song_id_folder(song=kwargs["song"])
        return f"{path}{filename}"

    async def get_local_song_id_folder(self, **kwargs) -> str:
        return f"{SONG_DATA_FOLDER}{self.game_title}/{kwargs['song'].songid}/"

    async def get_songs(self):
        return [x.title for x in SONG_LIST]

    async def get_song(self, **kwargs):
        return next(x for x in SONG_LIST if x.title.lower() == kwargs["title"].lower())

    async def get_difficulty(self, **kwargs):
        return next(x for x in kwargs["song"].difficulties if x.level == int(kwargs["difficulty"]))
