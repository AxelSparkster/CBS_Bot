import logging
import random
import requests
from discord.ext import commands
from typing import get_args
from bot.resources.models.animals import ANIMAL_LITERAL


def get_random_animal_image(animal: str) -> str:
    response = requests.get("https://api.tinyfox.dev/img.json", {'animal': animal})
    return "https://api.tinyfox.dev" + response.json().get("loc")


class AnimalsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.hybrid_command(name="possum", description="Get a random possum image. 2 times/user/day.")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def possum(self, ctx) -> None:
        await ctx.send(get_random_animal_image("poss"))

    @commands.hybrid_command(name="randomanimal", description="Get a random animal image. 1 time/user/day.")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def random_animal(self, ctx, animal: ANIMAL_LITERAL) -> None:
        await ctx.send(get_random_animal_image(animal))

    @commands.hybrid_command(name="truerandomanimal", description="Get a COMPLETELY random animal image."
                                                                  "1 time/user/day.")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def true_random_animal(self, ctx) -> None:
        random_animal = random.choice(get_args(ANIMAL_LITERAL))
        await ctx.send(get_random_animal_image(random_animal))

    @random_animal.error
    @possum.error
    @true_random_animal.error
    async def on_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send('Sorry, you\'re on cooldown! Try again in `{e:.1f}` seconds.'.format(e=error.retry_after),
                           ephemeral=True)


def setup(bot):
    logging.warning("Animals cog added.")
    bot.add_cog(AnimalsCog(bot))
