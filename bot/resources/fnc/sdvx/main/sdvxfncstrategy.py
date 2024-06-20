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
    def __init__(self, x1_h_px, x2_h_px, y1_w_px, spacing_px, bottom_cutoff_px, ocr_scale_multiplier,
                 measure_oob_tol, game_title):
        super(SdvxFncStrategy, self).__init__(x1_h_px, x2_h_px, y1_w_px, spacing_px, bottom_cutoff_px,
                                              ocr_scale_multiplier, measure_oob_tol, game_title)
        pass

    async def execute_strategy(self, ctx, **kwargs):
        song = kwargs["song"]
        difficulty = kwargs["difficulty"]
        bar_clip = kwargs["bar_clip"]

        await self.sanitize_inputs(ctx, song=song, difficulty=difficulty, bar_clip=bar_clip)
        selected_song = await self.get_song(song)
        selected_difficulty = await self.get_difficulty(selected_song, difficulty)
        bar_start, bar_end = await self.get_barclip(bar_clip)
        chart_url = await self.get_song_url(song=selected_song, difficulty=selected_difficulty)
        local_file_path = await self.download_image_file(song=selected_song, difficulty=selected_difficulty)

        measure_numbers: dict[int, int]
        if await self.measure_file_exists(song=selected_song, difficulty=selected_difficulty):
            measure_numbers = await self.get_measure_numbers_from_file(song=selected_song,
                                                                       difficulty=selected_difficulty)
        else:
            measure_numbers = await self.get_measure_numbers_from_image(local_file_path)
            await self.save_measure_numbers_to_file(measure_numbers, song=selected_song,
                                                    difficulty=selected_difficulty)

        measure_numbers_adjusted = await self.adjust_measures(measure_numbers)
        start_column, end_column = await self.get_columns_from_barclip(measure_numbers_adjusted, bar_start, bar_end)
        cropped_image_path = await self.crop_image(local_file_path, start_column, end_column)
        embed = await self.create_embed(cropped_image_path, chart_url, song=selected_song,
                                        difficulty=selected_difficulty)
        image_file = discord.File(cropped_image_path)
        await ctx.followup.send(embed=embed, file=image_file)

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
        path = (f'{SONG_DATA_FOLDER}{self.game_title}/{song.songid}/'
                f'{await self.map_chart_filename(song=song, difficulty=difficulty)}.png')
        if not os.path.isfile(path):
            # Cache the file if it doesn't exist.
            os.makedirs(f'{SONG_DATA_FOLDER}{self.game_title}/{song.songid}/', exist_ok=True)
            with open(path, "wb") as handler:
                handler.write(image)
        else:
            logging.warning(f"Cached file already found, using file {path}.")
        return path

    async def get_measure_numbers_from_image(self, file_path: str) -> dict[int, int]:
        return await super(SdvxFncStrategy, self).get_measure_numbers_from_image(file_path)

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

    async def crop_image(self, local_file_path: str, start_column: int, end_column: int) -> str:
        return await super(SdvxFncStrategy, self).crop_image(local_file_path, start_column, end_column)

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

        filename = await self.get_measure_file_name(song=song, difficulty=kwargs["difficulty"])
        test = os.path.isfile(f"{SONG_DATA_FOLDER}{self.game_title}/{song.songid}/{filename}")
        return test

    async def get_measure_numbers_from_file(self, **kwargs) -> dict[int, int]:
        song = kwargs["song"]

        filename = await self.get_measure_file_name(song=song, difficulty=kwargs["difficulty"])
        with open(f"{SONG_DATA_FOLDER}{self.game_title}/{song.songid}/{filename}") as fp:
            data = json.load(fp)
        return {int(key): value for key, value in data.items()}

    async def save_measure_numbers_to_file(self, measures: dict[int, int], **kwargs):
        song = kwargs["song"]

        filename = await self.get_measure_file_name(song=song, difficulty=kwargs["difficulty"])
        path = f"{SONG_DATA_FOLDER}{self.game_title}/{song.songid}/{filename}"
        os.makedirs(f"{SONG_DATA_FOLDER}{self.game_title}/{song.songid}/", exist_ok=True)
        with open(path, 'w') as fp:
            json.dump(measures, fp)

    @staticmethod
    async def get_songs():
        return [x.title for x in SONG_LIST]

    @staticmethod
    async def get_song(title: str):
        return next(x for x in SONG_LIST if x.title.lower() == title.lower())

    @staticmethod
    async def get_difficulty(song: Song, level: str):
        return next(x for x in song.difficulties if x.level == int(level))
