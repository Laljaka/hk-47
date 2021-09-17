import discord
from discord.ext import commands
from fmjson import *
import datetime


class feedback_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def feedback(self, ctx, *args):
        now = datetime.datetime.now()
        time = now.strftime("%m/%d/%Y, %H:%M:%S")
        print(ctx.author.name)
        print(ctx.guild.name)
        print(time)
        print(args)
        feedback = json_read('feedback')
        feedback[time] = {'Server name': ctx.guild.name, 'Author': ctx.author.name, 'Feedback text': ' '.join(args)}
        json_write('feedback', feedback)