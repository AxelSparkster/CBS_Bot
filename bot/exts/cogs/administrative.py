import logging
import discord
from discord.ext import commands
from bot.exts.database import set_bot_messages_ability


async def is_owner_or_admin(ctx) -> bool:
    return await ctx.bot.is_owner(ctx.author) or await ctx.permissions.administrator


class AdministrativeCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.bot):
        self.bot = bot
        self._last_member = None

    @commands.hybrid_command(name="sync", description="(Owner/Admin only) Syncs the command tree.")
    async def sync(self, ctx) -> None:
        if await is_owner_or_admin(ctx):
            await ctx.bot.tree.sync()
            logging.warning("Command tree synced.")
            await ctx.send("Command tree synced.")

    @commands.hybrid_command(name="shutup",
                             description="(Owner/Admin only) Disables the bot from messaging in the server.")
    async def shutup(self, ctx) -> None:
        if await is_owner_or_admin(ctx):
            logging.warning(f"Disabling messages for guild ID {ctx.message.guild.id}.")
            set_bot_messages_ability(False, ctx.message.guild.id)
            await ctx.send("Messages have been disabled.")

    @commands.hybrid_command(name="getupanddanceman",
                             description="(Owner/Admin only) Re-enables the bot's ability to message in the server.")
    async def getupanddanceman(self, ctx) -> None:
        if await is_owner_or_admin(ctx):
            logging.warning(f"Enabling messages for guild ID {ctx.message.guild.id}.")
            set_bot_messages_ability(True, ctx.message.guild.id)
            await ctx.send("Messages have been enabled.")

    @commands.hybrid_command(name="deletemessage",
                             description="(Owner/Admin only) Deletes a message sent by the bot.")
    async def deletemessage(self, ctx, message_id: str) -> None:
        if await is_owner_or_admin(ctx):
            logging.warning(f"Deleting message for guild ID {ctx.message.guild.id}, "
                            f"channel ID {ctx.message.channel.id}, "
                            f"message ID {ctx.message.id}.")
            message = await ctx.message.channel.fetch_message(message_id)

            # Only allow bot messages to be deleted.
            if message.author == ctx.bot.user:
                logging.warning(f"Message creator was the bot, deleting.")
                await message.delete()
            else:
                logging.warning(f"Message creator was not the bot, not deleting.")

            await ctx.send(f"Successfully deleted message {ctx.message.id}.", ephemeral=True)


def setup(bot):
    logging.warning("Administrative cog added.")
    bot.add_cog(AdministrativeCog(bot))
