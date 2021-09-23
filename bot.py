import discord
from misc.fmjson import *
from discord.ext import commands
import os
from dotenv import load_dotenv

from cogs.music_cog import music_cog
from cogs.feedback_cog import feedback_cog
from cogs.owner_cog import owner_cog

load_dotenv()

intents = discord.Intents.default()
intents.members = True


def get_prefix(client, message):
    prefixes = json_read('prefix')
    return prefixes[str(message.guild.id)]


client = commands.Bot(command_prefix=get_prefix, intents=intents)

client.add_cog(music_cog(client))
client.add_cog(feedback_cog(client))
client.add_cog(owner_cog(client))


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online,
                                 activity=discord.Activity(type=discord.ActivityType.listening,
                                                           name='the screams of meatbags'))
    print('Bot is ready as {0.user}'.format(client))


@client.event
async def on_guild_join(guild):
    prefixes = json_read('prefix')
    prefixes[str(guild.id)] = '?'
    json_write('prefix', prefixes)


@client.event
async def on_guild_remove(guild):
    prefixes = json_read('prefix')
    prefixes.pop(str(guild.id))
    json_write('prefix', prefixes)


@client.command()
@commands.has_guild_permissions(administrator=True)
@commands.guild_only()
async def change_prefix(ctx, prefix):
    """
    Command to change bot prefix
    """
    prefixes = json_read('prefix')
    prefixes[str(ctx.guild.id)] = prefix
    json_write('prefix', prefixes)
    await ctx.send(f'Prefix changed to {prefix}')


client.run(os.getenv("TOKEN"))
