import logging
import discord
from dateutil import tz
from discord.ext import commands

from bot.exts.database import get_last_match
from bot.resources.models.enums import MatchType
from bot.utils.detectionutils import get_match_term
from bot.utils.timeutils import convert_to_unix_time


class MessageDetectionCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.bot):
        self.bot = bot
        self._last_member = None

    @commands.hybrid_command(name="lastmessage",
                             description="Gets information about the last time something was mentioned. "
                             "1 time/user/day.")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def lastmessage(self, ctx, match_type: MatchType) -> None:
        if match_type == MatchType.NO_MATCH:
            await ctx.send('That\'s not a valid match type! Try sending one of the other ones.', ephemeral=True)
            return

        # Get details of last message
        #
        last_cbs_message = get_last_match(match_type, ctx.message.guild.id)
        last_cbs_message_link = (f'https://canary.discord.com/channels/{last_cbs_message["guild_id"]}/'
                                 f'{last_cbs_message["channel_id"]}/{last_cbs_message["message_id"]}')
        preface_message = (
            f'The last mention of {get_match_term(match_type)} was '
            f'{convert_to_unix_time(last_cbs_message["created_at"])}'
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
    async def on_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send('Sorry, you\'re on cooldown! Try again in `{e:.1f}` seconds.'.format(e=error.retry_after),
                           ephemeral=True)
        

def setup(bot):
    logging.warning("Message Detection cog added.")
    bot.add_cog(MessageDetectionCog(bot))
