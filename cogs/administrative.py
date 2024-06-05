import bson
import logging
import discord
from database import SETTINGS_COLLECTION
from discord.ext import commands


class AdministrativeCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.bot):
        self.bot = bot
        self._last_member = None

    @commands.hybrid_command(name="sync", description="(Owner/Admin only) Syncs the command tree.")
    async def sync(self, ctx) -> None:
        if await ctx.bot.is_owner(ctx.author) or await ctx.message.author.guild_permissions.administrator:
            await ctx.bot.tree.sync()
            logging.warning("Command tree synced.")
            await ctx.send("Command tree synced.")

    @commands.hybrid_command(name="shutup",
                            description="(Owner/Admin only) Disables the bot from messaging in the server.")
    async def shutup(self, ctx) -> None:
        if await ctx.bot.is_owner(ctx.author) or await ctx.message.author.guild_permissions.administrator:
            logging.warning(f"Disabling messages for guild ID {ctx.message.guild.id}.")
            SETTINGS_COLLECTION.update_one({"guild_id": bson.int64.Int64(ctx.message.guild.id)},
                                        {"$set": {"message_enabled": False}})
            await ctx.send("Messages have been disabled.")

    @commands.hybrid_command(name="getupanddanceman",
                            description="(Owner/Admin only) Re-enables the bot's ability to message in the server.")
    async def getupanddanceman(self, ctx) -> None:
        if await ctx.bot.is_owner(ctx.author) or await ctx.message.author.guild_permissions.administrator:
            logging.warning(f"Enabling messages for guild ID {ctx.message.guild.id}.")
            SETTINGS_COLLECTION.update_one({"guild_id": bson.int64.Int64(ctx.message.guild.id)},
                                        {"$set": {"message_enabled": True}})
            await ctx.send("Messages have been enabled.")


def setup(bot):
    logging.warning("Administrative cog added.")
    bot.add_cog(AdministrativeCog(bot))
