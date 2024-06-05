import bson
import discord
import logging
from dateutil import tz
from discord.ext import commands

from exts.database import MESSAGE_COLLECTION
from resources.models import MatchType
from utils.time import convert_to_unix_time
from utils.detection import get_match_term


class MessageDetectionCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.bot):
        self.bot = bot
        self._last_member = None

    @commands.hybrid_command(name="lastmessage",
                                description="Gets information about the last time something was mentioned. "
                                            "1 time/user/day.")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def lastmessage(self, ctx, match_type: MatchType) -> None:
        # Get details of last message
        #
        last_cbs_message = (MESSAGE_COLLECTION.find({"guild_id": bson.int64.Int64(ctx.message.guild.id),
                                                    "match_type": str(match_type)})
                            .sort({"created_at": -1}).limit(1).next())
        last_cbs_message_link = (f'https://canary.discord.com/channels/{last_cbs_message["guild_id"]}/'
                                f'{last_cbs_message["channel_id"]}/{last_cbs_message["message_id"]}')
        preface_message = (
            f'The last mention of {get_match_term(match_type)} was {convert_to_unix_time(last_cbs_message["created_at"])}'
            f'by <@{last_cbs_message["author_id"]}>, which was here: {last_cbs_message_link}\n\n')
        localized_date = last_cbs_message["created_at"].replace(tzinfo=tz.gettz('UTC')).astimezone(
            tz.gettz('America/Chicago'))

        # Create the message embed
        #
        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=f'{last_cbs_message["author"]}', icon_url=f'{last_cbs_message["avatar_url"]}')
        embed.add_field(name='Message', value=f'{last_cbs_message["message"]}', inline=False)
        embed.add_field(name='Date', value=f'{localized_date.strftime("%B %d, %Y %I:%M %p %Z%z")}', inline=False)
        embed.set_footer(text="Note: This message is sent silently and does not ping users.")

        await ctx.send(content=f'{preface_message}', embed=embed, silent=True)


    @lastmessage.error
    async def on_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send('Sorry, you\'re on cooldown! Try again in `{e:.1f}` seconds.'.format(e=error.retry_after),
                        ephemeral=True)
        

def setup(bot):
    logging.warning("Message Detection cog added.")
    bot.add_cog(MessageDetectionCog(bot))
