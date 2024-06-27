import discord
import logging
import typing
from typing import List
from thefuzz import process, utils
from discord import app_commands
from discord.ext import commands

from bot.resources.fnc.sdvx.main.sdvxfncstrategy import SdvxFncStrategy


class SdvxindexCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.strategy = SdvxFncStrategy(x1_left_px=42,
                                        x2_left_px=90,
                                        y1_bottom_px=35,
                                        y2_bottom_px=0,
                                        spacing_px=254,
                                        doubles_spacing_px=None,
                                        bottom_cutoff_px=11,
                                        ocr_scale_multiplier=2,
                                        measure_oob_tol=20,
                                        game_title="sdvx")

    async def song_autocomplete(self, interaction: discord.Interaction, current: str) \
            -> List[discord.app_commands.Choice[str]]:
        song_names = await self.strategy.get_songs()
        if utils.full_process(current):
            closest_matches = process.extract(current, song_names, limit=25)
            return [
                app_commands.Choice(name=x[0], value=x[0])
                for x in closest_matches
                ]

    async def difficulty_autocomplete(self, interaction: discord.Interaction, current: str) \
            -> List[discord.app_commands.Choice[str]]:
        song_title = interaction.namespace.song
        song = await self.strategy.get_song(title=song_title)
        difficulties = [x for x in song.difficulties]
        return [
            app_commands.Choice(name=f"{await self.strategy.map_chart_name(level_type=x.type)} {x.level}",
                                value=str(x.level))
            for x in difficulties
            ]

    @app_commands.command(name="sdvxindex", description="Retrieve a chart from https://sdvxindex.com/.")
    @app_commands.describe(song="Start typing for a list of suggestions based on your input.")
    @app_commands.describe(difficulty="Choose a difficulty for the song.")
    @app_commands.describe(bar_clip="Select a portion of the song, for example 20-30. The default is 1-15.")
    @app_commands.autocomplete(song=song_autocomplete, difficulty=difficulty_autocomplete)
    async def sdvxindex(self, ctx, song: str, difficulty: str, bar_clip: typing.Optional[str]) -> None:
        await ctx.response.defer()
        await self.strategy.execute_strategy(ctx, song=song, difficulty=difficulty, bar_clip=bar_clip)


def setup(bot):
    logging.warning("Sdvxindex cog added.")
    bot.add_cog(SdvxindexCog(bot))
