import json
import logging
import os
import re

import discord
import msgspec
import pytesseract
import requests

from discord import Embed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from unidecode import unidecode

from bot.resources.fnc.ddr.ddrfncmodels import DdrSong
from bot.resources.fnc.ddr.songdata import DDR_SONGS
from bot.resources.fnc.fncconstants import SONG_DATA_FOLDER, OUTPUT_FILE_NAME, DEFAULT_BARCLIP, BARCLIP_REGEX
from bot.resources.fnc.fncstrategy import FncStrategy
from bot.resources.fnc.ddr.ddrfncmodels import LEVEL_MAPPINGS, VERSION_MAPPINGS
from definitions import SELENIUM_URL

SONG_LIST: list[DdrSong] = msgspec.json.decode(DDR_SONGS, type=list[DdrSong])

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'


class ThreeIceCreamStrategy(FncStrategy):
    def __init__(self, x1_left_px, x2_left_px, y1_bottom_px, y2_bottom_px, spacing_px, bottom_cutoff_px,
                 ocr_scale_multiplier, measure_oob_tol, game_title):
        super(ThreeIceCreamStrategy, self).__init__(x1_left_px, x2_left_px, y1_bottom_px, y2_bottom_px, spacing_px,
                                                    bottom_cutoff_px, ocr_scale_multiplier, measure_oob_tol, game_title)
        pass

    async def execute_strategy(self, ctx, **kwargs):
        await super(ThreeIceCreamStrategy, self).execute_strategy(ctx, **kwargs)

    async def map_chart_name(self, **kwargs) -> str:
        level_type = kwargs["level_type"]

        for word, info in LEVEL_MAPPINGS.items():
            level_type = level_type.replace(word.lower(), info["shorthand"])
        return level_type

    async def get_barclip(self, bar_clip: str):
        return await super(ThreeIceCreamStrategy, self).get_barclip(bar_clip)

    async def map_chart_type(self, **kwargs) -> str:
        return ""

    async def map_chart_filename(self, **kwargs) -> str:
        return f"{kwargs['song'].song_id}-{kwargs['difficulty']['name']}"

    async def download_image_file(self, **kwargs) -> str:
        song = kwargs["song"]
        difficulty = kwargs["difficulty"]

        url = await self.get_song_url(song=song, difficulty=difficulty)
        filename = await self.get_local_song_id_folder_plus_filename(song=song, difficulty=difficulty) + ".png"
        path = await self.get_local_song_id_folder(song=song)

        if os.path.isfile(filename):
            logging.warning(f"Cached file already found, using file {filename}.")
            return filename

        try:
            # 3icecream is weird, the chart only lives server-side for a handful of seconds once the chart's page has
            # been accessed. Therefore, we need to use Selenium to load the page and just grab the image while it's
            # still existent using our "usual" method.
            logging.warning(f"Creating WebDriver.")
            options = Options()
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--headless")
            options.add_argument('--disable-gpu')
            user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                          'like Gecko) Chrome/83.0.4103.116 Safari/537.36')
            options.add_argument(f'user-agent={user_agent}')
            driver = webdriver.Remote(options=options, command_executor=SELENIUM_URL)

            try:
                logging.warning(f"Attempting to get page at {url}.")
                driver.get(url)
                ba = driver.find_element(By.XPATH, '/html/body/img')
                image = requests.get(ba.get_attribute('src')).content
                logging.warning(f"Image attributes successfully retrieved, downloading file {image}.")
                if not os.path.isfile(filename):
                    # Cache the file if it doesn't exist.
                    os.makedirs(path, exist_ok=True)
                    with open(filename, "wb") as handler:
                        handler.write(image)
                else:
                    logging.warning(f"Cached file already found, using file {filename}.")
                driver.quit()
                logging.warning(f"Successfully downloaded image. Local path: {filename}.")
                return filename
            except Exception as e:
                logging.warning(f"Error occurred getting image. Error: {e}.")
                driver.quit()
                raise e

        except Exception as e:
            logging.warning(f"Error occurred creating driver. Error: {e}.")
            raise e

    async def get_measure_numbers_from_image(self, file_path: str) -> dict[int, int]:
        return await super(ThreeIceCreamStrategy, self).get_measure_numbers_from_image(file_path)

    async def adjust_measures(self, column_dict: dict[int, int]) -> dict[int, int]:
        return await super(ThreeIceCreamStrategy, self).adjust_measures(column_dict)

    async def get_columns_from_barclip(self, column_dict: dict[int, int], bar_start: str, bar_end: str):
        return await super(ThreeIceCreamStrategy, self).get_columns_from_barclip(column_dict, bar_start, bar_end)

    async def sanitize_inputs(self, ctx, **kwargs):
        try:
            selected_song = next(x for x in SONG_LIST if x.song_name.lower() == kwargs["song"].lower())
        except StopIteration:
            return await ctx.response.send_message("Not really sure what song that is. Try using the "
                                                   "autocomplete function and don't edit the results!", ephemeral=True)

        try:
            if not (0 <= int(kwargs["difficulty"]["rating_index"]) < len(selected_song.ratings)):
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
        return (f"https://3icecream.com/ren/chart?songId={kwargs['song'].song_id}"
                f"&speedmod=2&diff={kwargs['difficulty']['rating_index']}")

    async def crop_image(self, local_file_path: str, start_column: int, end_column: int) -> str:
        return await super(ThreeIceCreamStrategy, self).crop_image(local_file_path, start_column, end_column)

    async def create_embed(self, cropped_image_path: str, chart_url: str, **kwargs) -> Embed:
        song = kwargs["song"]
        difficulty = kwargs["difficulty"]

        embed = discord.Embed(color=LEVEL_MAPPINGS[difficulty["full_name"]]["color"])
        embed.set_author(name=f'{song.song_name} ({difficulty["name"]} {difficulty["level"]})')
        embed.set_thumbnail(url=f'https://3icecream.com/img/banners/f/{song.song_id}.jpg')
        embed.add_field(name='Version First Appeared', value=f'{VERSION_MAPPINGS[song.version_num]}', inline=False)
        embed.add_field(name='3icecream URL', value=f'[link to chart]({chart_url})', inline=False)
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
        return f"{SONG_DATA_FOLDER}{self.game_title}/{kwargs['song'].song_id}/"

    async def get_songs(self):
        return [x.song_name for x in SONG_LIST]

    async def get_song(self, **kwargs):
        return next(x for x in SONG_LIST if x.song_name.lower() == kwargs["title"].lower())

    async def get_difficulty(self, **kwargs):
        return kwargs["difficulty"]

    @staticmethod
    async def map_ratings_to_dict(rating_list: list[int]) -> dict[int, dict[str, str | int]]:
        new_rating_dict = dict()
        for i in range(0, len(rating_list)):  # TODO: something more elegant?
            if rating_list[i] == 0:
                continue
            left = ""
            difficulty = ""
            match i:
                case 0:
                    difficulty = "beginner"
                    left = "b"
                case 1 | 5:
                    difficulty = "basic"
                    left = "B"
                case 2 | 6:
                    difficulty = "difficult"
                    left = "D"
                case 3 | 7:
                    difficulty = "expert"
                    left = "E"
                case 4 | 8:
                    difficulty = "challenge"
                    left = "C"
            middle = "S" if i <= 4 else "D"
            rating = f"{left}{middle}P"
            new_rating_dict[i] = {'name': rating, 'level': rating_list[i], 'full_name': difficulty, 'rating_index': i}
        return new_rating_dict
