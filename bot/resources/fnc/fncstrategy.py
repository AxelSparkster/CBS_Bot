import logging
import re
import cv2
import discord
import numpy
import pytesseract
from abc import ABC, abstractmethod
from discord import Embed
from unidecode import unidecode

from bot.resources.fnc.fncconstants import SONG_DATA_FOLDER, OUTPUT_FILE_NAME, DEFAULT_BARCLIP, BARCLIP_REGEX

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'


class FncStrategy(ABC):
    @abstractmethod
    def __init__(self, x1_left_px, x2_left_px, y1_bottom_px, spacing_px, bottom_cutoff_px, ocr_scale_multiplier,
                 measure_oob_tol, game_title):
        """
        Notes:
        x1_left_px - The number, in pixels, from the top left corner of the ROI (Region of Interest)
            to the LEFT side of the image.
        x2_left_px - The number, in pixels, from the bottom right corner of the ROI
            to the LEFT side of the image.
        y1_bottom_px - The number, in pixels, from the top left corner of the ROI
            to the BOTTOM side of the image.
        ocr_scale_multiplier - The multiplier of how much the image should be scaled by to get better
            readability for the numbers. NOTE: A bigger number means the process may take longer.
        spacing_px - The number, in pixels, between each number.
        measure_oob_tol - The number in which the change in difference between measures is too substantial,
            and will be recalculated using (the last measure number + the average difference).
        game_title - The name of the game. This will be used to create a specialized folder to store
            chart images as well as their measure information.
        """
        self.x1_left_px = x1_left_px
        self.x2_left_px = x2_left_px
        self.y1_bottom_px = y1_bottom_px
        self.spacing_px = spacing_px
        self.bottom_cutoff_px = bottom_cutoff_px
        self.ocr_scale_multiplier = ocr_scale_multiplier
        self.measure_oob_tol = measure_oob_tol
        self.game_title = game_title

    @abstractmethod
    async def execute_strategy(self, ctx, **kwargs):
        # Execute the strategy that will take the user's input and create the bot message.
        song = kwargs["song"]
        difficulty = kwargs["difficulty"]
        bar_clip = kwargs["bar_clip"]

        await self.sanitize_inputs(ctx, song=song, difficulty=difficulty, bar_clip=bar_clip)
        selected_song = await self.get_song(title=song)
        selected_difficulty = await self.get_difficulty(song=selected_song, difficulty=difficulty)
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

    @abstractmethod
    async def map_chart_name(self, **kwargs) -> str:
        # Maps the chart to its shorthand name. For example, Voltex's shorthand for "Exhaust" is "EXH", and for
        # IIDX, "Single Another 8" is "SP8". The implementation will depend on the strategy since we may choose
        # shorthands differ between games.
        raise NotImplementedError

    @abstractmethod
    async def map_chart_type(self, **kwargs) -> str:
        # Maps the chart to a type. A "type" is a special shorthand used in URLs. The implementation will
        # depend on the strategy since the way a site builds up URLs will differ.
        raise NotImplementedError

    @abstractmethod
    async def map_chart_filename(self, **kwargs) -> str:
        # Maps the chart to a filename. The implementation will depend on the strategy since we may choose
        # a different filename depending on the chosen game.
        raise NotImplementedError

    @abstractmethod
    async def download_image_file(self, **kwargs):
        # Downloads the image file locally, and merges images before saving if necessary. The implementation
        # will depend on the strategy since this process can differ.
        raise NotImplementedError

    @abstractmethod
    async def sanitize_inputs(self, ctx, **kwargs):
        # Checks the arguments of the Discord command. The number of arguments will differ as different commands
        # may take in different inputs.
        raise NotImplementedError

    @abstractmethod
    async def get_barclip(self, bar_clip: str):
        if bar_clip is None:
            bar_clip = DEFAULT_BARCLIP
        result = re.search(BARCLIP_REGEX, unidecode(bar_clip))
        bar_clip_start = result.group(1)
        bar_clip_end = result.group(2)
        return bar_clip_start, bar_clip_end

    @abstractmethod
    async def get_song_url(self, **kwargs) -> str:
        # Creates the song URL for a given site given its song and chart information.
        # This will depend on the strategy's implementation, as different sites will have different URLS and
        # methodologies for creating accessing each chart.
        raise NotImplementedError

    @abstractmethod
    async def measure_file_exists(self, **kwargs) -> bool:
        # Checks to see if measures exist from a previous run, and uses those to save time. Unfortunately, the file
        # name may change based off of chart information, so we can't make this generic.
        raise NotImplementedError

    @abstractmethod
    async def get_measure_numbers_from_file(self, **kwargs) -> dict[int, int]:
        # Gets the measures from a previously saved file. Unfortunately, the file name may change based off of
        # chart information, so we can't make this generic.
        raise NotImplementedError

    @abstractmethod
    async def save_measure_numbers_to_file(self, measures: dict[int, int], **kwargs):
        # Saves the measures to a file. Unfortunately, the file name may change based off of chart information,
        # so we can't make this generic.
        raise NotImplementedError

    @abstractmethod
    async def get_measure_numbers_from_image(self, file_path: str) -> dict[int, int]:
        # Downloads the image from a given website and merges the chart and measure numbers together (if applicable).

        resize_value = self.ocr_scale_multiplier
        column_width = self.spacing_px * resize_value
        roi_x1_begin = self.x1_left_px * resize_value
        roi_x2_begin = self.x2_left_px * resize_value
        roi_y1_begin = self.y1_bottom_px * resize_value

        # Pre-process image for Tesseract.
        img = cv2.imread(file_path)
        img_rsz = cv2.resize(img, (0, 0), fx=resize_value, fy=resize_value)
        h, w, c = img_rsz.shape
        img_rct = cv2.rectangle(img_rsz, (0, h - self.bottom_cutoff_px * resize_value), (w, h), (0, 0, 0), -1)
        gray_image = cv2.cvtColor(img_rct, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Get basic details about the image, so we can loop over
        # each column to check the measure numbers.
        columns = round(w / column_width)

        # Loop over each ROI and get the text. First column always starts with 1.
        column_dict: dict[int, int] = {0: 1}
        for column_num in range(1, columns):
            roi_x_1 = roi_x1_begin + (column_num * column_width)
            roi_y_1 = h - roi_y1_begin
            roi_x_2 = roi_x2_begin + (column_num * column_width)
            roi_y_2 = h
            roi = thresh[roi_y_1:roi_y_2, roi_x_1:roi_x_2]
            data = pytesseract.image_to_string(roi, lang='eng', config='--psm 10 --oem 3 -c '
                                                                       'tessedit_char_whitelist=0123456789').strip()
            measure_number = 0  # By default, assume it's nothing - we can always fix it later in adjust_measures().
            if data != "":
                measure_number = int(data)
            column_dict[column_num] = measure_number
        return column_dict

    @abstractmethod
    async def adjust_measures(self, column_dict: dict[int, int]) -> dict[int, int]:
        # OCR can be unreliable, so try to guess/fix the measures if they seem off.

        # Get the average difference between measures.
        new_dict = column_dict.copy()
        avg_measures = round(numpy.diff(list(new_dict.values())).sum() / (len(new_dict) - 1))
        for i in range(len(new_dict)):
            if i == 0:
                continue  # First value is always 1 by default, skip.
            if new_dict[i] <= new_dict[i-1] or new_dict[i] - new_dict[i-1] >= self.measure_oob_tol:
                new_dict[i] = new_dict[i-1] + avg_measures
        return new_dict

    @abstractmethod
    async def get_columns_from_barclip(self, column_dict: dict[int, int], bar_start: str, bar_end: str):
        # Gets the beginning and end column numbers based off of the measures wanted.
        start_column = next((x for x in reversed(column_dict) if column_dict[x] <= int(bar_start)), None)
        end_column = next((x for x in column_dict if column_dict[x] >= int(bar_end)), None)
        return start_column, end_column

    @abstractmethod
    async def crop_image(self, local_file_path: str, start_column: int, end_column: int) -> str:
        # Crops the image based off of the characteristics given during strategy creation.
        img = cv2.imread(local_file_path)
        h, w, c = img.shape
        crop_x_start = self.spacing_px * start_column
        crop_x_end = self.spacing_px * end_column
        crop = img[0:h, crop_x_start:crop_x_end]
        cv2.imwrite(f"{SONG_DATA_FOLDER}/{self.game_title}/{OUTPUT_FILE_NAME}", crop)
        return f"{SONG_DATA_FOLDER}/{self.game_title}/{OUTPUT_FILE_NAME}"

    @abstractmethod
    async def create_embed(self, cropped_image_path: str, chart_url: str, **kwargs) -> Embed:
        # Creates the Discord embed to be posted by the bot.
        # This will depend on the strategy's implementation, as different games may have the need for
        # different information being shown.
        raise

    @abstractmethod
    async def get_local_song_id_folder(self) -> str:
        # Builds up the location of the Song ID folder on the drive.
        raise NotImplementedError

    @abstractmethod
    async def get_songs(self):
        # Gets the information about all Songs for the given game. This is used for autocompletion.
        raise NotImplementedError

    @abstractmethod
    async def get_song(self, **kwargs):
        # Gets the information about a single Song object (the Song object may look different from
        # game to game).
        raise NotImplementedError

    @abstractmethod
    async def get_difficulty(self, **kwargs):
        # Gets the information about a single Difficulty object based on a selected Song
        # (the Difficulty object may look different from game to game).
        raise NotImplementedError
