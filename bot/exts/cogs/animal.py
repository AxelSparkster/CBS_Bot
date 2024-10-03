import discord
import logging
import random
import requests
import numpy as np
from discord.ext import commands
from typing import get_args
from bot.resources.models.animals import ANIMAL_LITERAL, RATING_MAPPINGS


def get_random_animal_image(animal: str) -> str:
    response = requests.get("https://api.tinyfox.dev/img.json", {'animal': animal})
    return "https://api.tinyfox.dev" + response.json().get("loc")


def n(rating: str) -> str:
    if rating == 'A':
        return 'n'
    else:
        return ''

def create_animal_embed(url: str) -> discord.Embed:
    rating = get_rating()
    color = RATING_MAPPINGS[rating]["color"]
    logging.warning(f"Color: {color}.")
    embed = discord.Embed(color=RATING_MAPPINGS[rating]["color"],
                          title=f'Congratulations!',
                          description=f'You rolled a{n(rating)} **{rating}** tier animal.')
    embed.set_image(url=url)
    return embed


def get_rating() -> str:
    ratings = ['SSS+', 'SSS', 'SS+', 'SS', 'S+', 'S', 'A', 'B', 'C', 'D']
    weights = [0.0001, 0.0005, 0.001, 0.03, 0.05, 0.1, 0.5, 0.2, 0.1, 0.0184]
    random_rating = np.random.choice(ratings, 1, p=weights)
    return str(random_rating[0])


class AnimalsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.hybrid_command(name="possum", description="Get a random possum image. 2 times/user/day.")
    @commands.cooldown(1, 86400, commands.BucketType.member)
    async def possum(self, ctx) -> None:
        await ctx.send(get_random_animal_image("poss"))

    @commands.hybrid_command(name="randomanimal", description="Get a random animal image. 1 time/user/day.")
    @commands.cooldown(1, 86400, commands.BucketType.member)
    async def random_animal(self, ctx, animal: ANIMAL_LITERAL) -> None:
        await ctx.send(get_random_animal_image(animal))

    @commands.hybrid_command(name="truerandomanimal", description="Get a COMPLETELY random animal image."
                                                                  "1 time/user/day.")
    @commands.cooldown(1, 86400, commands.BucketType.member)
    async def true_random_animal(self, ctx) -> None:
        random_animal = random.choice(get_args(ANIMAL_LITERAL))
        url = get_random_animal_image(random_animal)
        await ctx.send(embed=create_animal_embed(url))

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
