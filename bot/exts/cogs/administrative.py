import logging
import discord
from discord.ext import commands
from bot.exts.database import set_bot_messages_ability


async def is_owner_or_admin(ctx) -> bool:
    return await ctx.bot.is_owner(ctx.author) or await ctx.message.author.guild_permissions.administrator


class AdministrativeCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.bot):
        self.bot = bot
        self._last_member = None

    @commands.hybrid_command(name="sync", description="(Owner/Admin only) Syncs the command tree.")
    async def sync(self, ctx) -> None:
        if is_owner_or_admin(ctx):
            await ctx.bot.tree.sync()
            logging.warning("Command tree synced.")
            await ctx.send("Command tree synced.")

    @commands.hybrid_command(name="shutup",
                             description="(Owner/Admin only) Disables the bot from messaging in the server.")
    async def shutup(self, ctx) -> None:
        if is_owner_or_admin(ctx):
            logging.warning(f"Disabling messages for guild ID {ctx.message.guild.id}.")
            set_bot_messages_ability(False, ctx.message.guild.id)
            await ctx.send("Messages have been disabled.")

    @commands.hybrid_command(name="getupanddanceman",
                             description="(Owner/Admin only) Re-enables the bot's ability to message in the server.")
    async def getupanddanceman(self, ctx) -> None:
        if is_owner_or_admin(ctx):
            logging.warning(f"Enabling messages for guild ID {ctx.message.guild.id}.")
            set_bot_messages_ability(True, ctx.message.guild.id)
            await ctx.send("Messages have been enabled.")


def setup(bot):
    logging.warning("Administrative cog added.")
    bot.add_cog(AdministrativeCog(bot))
