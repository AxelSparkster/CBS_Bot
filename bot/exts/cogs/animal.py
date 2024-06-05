import logging
import requests
from discord.ext import commands
from typing import Literal

ANIMAL_LITERAL = Literal["fox", "yeen", "dog", "snek", "poss", "leo", "serval", "bleat",
                         "shiba", "racc", "dook", "ott", "snep", "woof", "capy", "bear", "bun",
                         "caracal", "puma", "mane", "marten", "tig", "skunk", "jaguar", "yote"]


def get_random_animal_image(animal: str) -> str:
    # Gets URL of random animal image.
    params = {'animal': animal}
    response = requests.get("https://api.tinyfox.dev/img.json", params)
    animal_url = "https://api.tinyfox.dev" + response.json().get("loc")
    return animal_url


class AnimalsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.hybrid_command(name="possum", description="Get a random possum image. 2 times/user/day.")
    @commands.cooldown(2, 86400, commands.BucketType.user)
    async def possum(self, ctx) -> None:
        await ctx.send(get_random_animal_image("poss"))

    @commands.hybrid_command(name="randomanimal", description="Get a random animal image. 1 time/user/day.")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def random_animal(self, ctx, animal: ANIMAL_LITERAL) -> None:
        await ctx.send(get_random_animal_image(animal))

    @random_animal.error
    @possum.error
    async def on_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send('Sorry, you\'re on cooldown! Try again in `{e:.1f}` seconds.'.format(e=error.retry_after),
                           ephemeral=True)


def setup(bot):
    logging.warning("Animals cog added.")
    bot.add_cog(AnimalsCog(bot))
