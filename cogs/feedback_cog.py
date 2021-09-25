from discord.ext import commands
from misc.fmjson import *
import datetime


class feedback_cog(commands.Cog, name='Feedback'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def feedback(self, ctx, *your_message):
        """
        Leaves a feedback or a bug report
        """
        now = datetime.datetime.now()
        time = now.strftime("%m/%d/%Y, %H:%M:%S")
        print(ctx.author.name)
        print(ctx.guild.name)
        print(time)
        print(your_message)
        feedback = json_read('feedback')
        feedback[time] = {'Server name': ctx.guild.name, 'Author': ctx.author.name, 'Feedback text': ' '.join(args)}
        json_write('feedback', feedback)
