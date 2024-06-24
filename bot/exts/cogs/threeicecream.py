import discord
import logging
import typing
from typing import List
from thefuzz import process, utils
from discord import app_commands
from discord.ext import commands

from bot.resources.fnc.ddr.threeicecreamstrategy import ThreeIceCreamStrategy


class ThreeIceCreamCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.strategy = ThreeIceCreamStrategy(x1_left_px=0,
                                              x2_left_px=19,
                                              y1_bottom_px=915,
                                              y2_bottom_px=889,
                                              spacing_px=160,
                                              bottom_cutoff_px=24,
                                              ocr_scale_multiplier=2,
                                              measure_oob_tol=5,
                                              game_title="ddr")

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
        difficulties = [x for x in song.ratings]
        return [
            app_commands.Choice(name=f"{x['name']} {x['level']}", value=str(x['rating_index']))
            for x in (await self.strategy.map_ratings_to_dict(difficulties)).values()
            ]

    @app_commands.command(name="threeicecream", description="Retrieve a chart from https://3icecream.com/.")
    @app_commands.describe(song="Start typing for a list of suggestions based on your input.")
    @app_commands.describe(difficulty="Choose a difficulty for the song.")
    @app_commands.describe(bar_clip="Select a portion of the song, for example 20-30. The default is 1-15.")
    @app_commands.autocomplete(song=song_autocomplete, difficulty=difficulty_autocomplete)
    async def threeicecream(self, ctx, song: str, difficulty: str, bar_clip: typing.Optional[str]) -> None:
        await ctx.response.defer()

        # Unfortunately, 3icecream stores ratings just as a list of integers, with no identifying information...
        # so we're just going to build that up before sending it down the pipeline
        difficulties = [x for x in (await self.strategy.get_song(title=song)).ratings]
        obj_difficulty = (await self.strategy.map_ratings_to_dict(difficulties))[int(difficulty)]

        await self.strategy.execute_strategy(ctx, song=song, difficulty=obj_difficulty, bar_clip=bar_clip)


def setup(bot):
    logging.warning("3icecream cog added.")
    bot.add_cog(ThreeIceCreamCog(bot))
