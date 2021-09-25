import discord
from discord.ext import commands
from misc.fmjson import *


class owner_cog(commands.Cog, name='Owner stuff'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def check_registered(self, ctx):
        for guild in self.bot.guilds:
            print(guild.name)
            print(guild.id)
            print(guild.owner.name)
            print('----------------------------')

    @commands.command()
    @commands.is_owner()
    async def leave_unregistered(self, ctx):
        prefixes = json_read('prefix')
        keys = prefixes.keys()
        new_keys = []
        for key in keys:
            new_keys.append(int(key))
        for guild in self.bot.guilds:
            if guild.id not in new_keys:
                await guild.leave()

    @commands.command()
    @commands.is_owner()
    async def register(self, ctx):
        prefixes = json_read('prefix')
        keys = prefixes.keys()
        new_keys = []
        for key in keys:
            new_keys.append(int(key))
        for guild in self.bot.guilds:
            if guild.id not in new_keys:
                prefixes[str(guild.id)] = '?'
        json_write('prefix', prefixes)

    @commands.command()
    @commands.is_owner()
    async def ping(self, ctx):
        """
        Test command to get latency
        """
        await ctx.send(f'{round(self.bot.latency * 1000)}ms')

    @commands.command()
    @commands.is_owner()
    async def logout(self, ctx):
        await self.bot.logout()


