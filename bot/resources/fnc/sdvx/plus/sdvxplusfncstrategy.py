import discord
import logging
import msgspec
import os
import requests
import re
from discord import Embed
from unidecode import unidecode

from bot.resources.fnc.sdvx.main.sdvxfncstrategy import SdvxFncStrategy
from bot.resources.fnc.sdvx.plus.songdataplus import SONGSPLUS
from bot.resources.fnc.sdvx.sdvxfncmodels import SongPlus, LEVEL_MAPPINGS
from bot.resources.fnc.fncconstants import DEFAULT_BARCLIP, BARCLIP_REGEX, SONG_DATA_FOLDER, OUTPUT_FILE_NAME, \
    SDVXPLUS_CLOUDFRONT

SONG_LIST: list[SongPlus] = msgspec.json.decode(SONGSPLUS, type=list[SongPlus])


class SdvxPlusFncStrategy(SdvxFncStrategy):
    def __init__(self, x1_left_px, x2_left_px, y1_bottom_px, y2_bottom_px, spacing_px, bottom_cutoff_px,
                 ocr_scale_multiplier, measure_oob_tol, game_title):
        super(SdvxPlusFncStrategy, self).__init__(x1_left_px, x2_left_px, y1_bottom_px, y2_bottom_px, spacing_px,
                                                  bottom_cutoff_px, ocr_scale_multiplier, measure_oob_tol, game_title)
        pass

    async def execute_strategy(self, ctx, **kwargs):
        return await super(SdvxPlusFncStrategy, self).execute_strategy(ctx, **kwargs)

    async def map_chart_name(self, **kwargs) -> str:
        return await super(SdvxPlusFncStrategy, self).map_chart_name(**kwargs)

    async def get_barclip(self, bar_clip: str):
        return await super(SdvxPlusFncStrategy, self).get_barclip(bar_clip)

    async def map_chart_type(self, **kwargs) -> str:
        # Not needed for Plus.
        raise NotImplementedError

    async def map_chart_filename(self, **kwargs) -> str:
        return f"{kwargs['song'].id}-{kwargs['difficulty'].idx}"

    async def download_image_file(self, **kwargs) -> str:
        song = kwargs["song"]
        difficulty = kwargs["difficulty"]

        image = requests.get(f'{SDVXPLUS_CLOUDFRONT}{str(song.id).zfill(4)}/r_{difficulty.idx}.png').content
        path = (f'{SONG_DATA_FOLDER}{self.game_title}/{str(song.id).zfill(4)}/'
                f'{await self.map_chart_filename(song=song, difficulty=difficulty)}.png')
        if not os.path.isfile(path):
            # Cache the file if it doesn't exist.
            os.makedirs(f'{SONG_DATA_FOLDER}{self.game_title}/{str(song.id).zfill(4)}/', exist_ok=True)
            with open(path, "wb") as handler:
                handler.write(image)
        else:
            logging.warning(f"Cached file already found, using file {path}.")
        return path

    async def get_measure_numbers_from_image(self, file_path: str) -> dict[int, int]:
        return await super(SdvxPlusFncStrategy, self).get_measure_numbers_from_image(file_path)

    async def adjust_measures(self, column_dict: dict[int, int]) -> dict[int, int]:
        return await super(SdvxPlusFncStrategy, self).adjust_measures(column_dict)

    async def get_columns_from_barclip(self, column_dict: dict[int, int], bar_start: str, bar_end: str):
        return await super(SdvxPlusFncStrategy, self).get_columns_from_barclip(column_dict, bar_start, bar_end)

    async def sanitize_inputs(self, ctx, **kwargs):
        try:
            selected_song = next(x for x in SONG_LIST if x.title.lower() == kwargs["song"].lower())
        except StopIteration:
            return await ctx.response.send_message("Not really sure what song that is. Try using the "
                                                   "autocomplete function and don't edit the results!", ephemeral=True)

        try:
            if int(kwargs["difficulty"]) not in [x.level for x in selected_song.diffs]:
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
        return f"https://sdvxplus.zip/unzip/{kwargs['song'].id}/{kwargs['difficulty'].idx}"

    async def crop_image(self, local_file_path: str, start_column: int, end_column: int) -> str:
        return await super(SdvxPlusFncStrategy, self).crop_image(local_file_path, start_column, end_column)

    async def create_embed(self, cropped_image_path: str, chart_url: str, **kwargs) -> Embed:
        song = kwargs["song"]
        difficulty = kwargs["difficulty"]

        color = next(x for x in LEVEL_MAPPINGS.values() if x["shorthand"].lower() == difficulty.name.lower())["color"]

        embed = discord.Embed(color=color)
        embed.set_author(name=f'{song.title} ({difficulty.name} {difficulty.level})')
        embed.set_thumbnail(url=f'{SDVXPLUS_CLOUDFRONT}{difficulty.jacketPath}')
        embed.add_field(name='Song Artist', value=f'{song.artist}')
        embed.add_field(name='Effected By', value=f'{difficulty.effector}')
        embed.add_field(name='sdvxplus URL', value=f'{await self.get_song_url(song=song, difficulty=difficulty)}',
                        inline=False)
        embed.set_image(url=f'attachment://{OUTPUT_FILE_NAME}')
        return embed

    async def get_measure_file_name(self, **kwargs):
        return await super(SdvxPlusFncStrategy, self).get_measure_file_name(**kwargs)

    async def measure_file_exists(self, **kwargs) -> bool:
        return await super(SdvxPlusFncStrategy, self).measure_file_exists(**kwargs)

    async def get_measure_numbers_from_file(self, **kwargs) -> dict[int, int]:
        return await super(SdvxPlusFncStrategy, self).get_measure_numbers_from_file(**kwargs)

    async def save_measure_numbers_to_file(self, measures: dict[int, int], **kwargs):
        return await super(SdvxPlusFncStrategy, self).save_measure_numbers_to_file(measures, **kwargs)

    async def get_local_song_id_folder_plus_filename(self, **kwargs) -> str:
        return await super(SdvxPlusFncStrategy, self).get_local_song_id_folder_plus_filename(**kwargs)

    async def get_local_song_id_folder(self, **kwargs) -> str:
        return f"{SONG_DATA_FOLDER}{self.game_title}/{str(kwargs['song'].id).zfill(4)}/"

    async def get_songs(self):
        return [x.title for x in SONG_LIST]

    async def get_song(self, **kwargs):
        return next(x for x in SONG_LIST if x.title.lower() == kwargs["title"].lower())

    async def get_difficulty(self, **kwargs):
        return next(x for x in kwargs["song"].diffs if x.level == int(kwargs["difficulty"]))
