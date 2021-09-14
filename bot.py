import discord
import json
from discord.ext import commands
import os
from dotenv import load_dotenv
import youtube_dl
#import emojis
#from datetime import datetime
load_dotenv()

#Variables
intents = discord.Intents.default()
intents.members = True

#reads json
def json_read(filename):
    with open(f'{filename}.json', 'r') as f:
        print(f)
        data = json.load(f)
    return data
#writes to json
def json_write(filename, data):
    with open(f'{filename}.json', 'w') as f:
        json.dump(data, f, indent =4)
#important DO NOT CHANGE
def get_prefix(client, message):
    prefixes = json_read('prefix')
    return prefixes[str(message.guild.id)]

#important DO NOT CHANGE
client = commands.Bot(command_prefix = get_prefix, intents = intents)

#important DO NOT CHANGE
#Ready check
@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.listening, name='the screams of meatbags'))
    print('Bot is ready as {0.user}'.format(client))

#important DO NOT CHANGE
#Joining the server and creating a prefix in json file
@client.event
async def on_guild_join(guild):
    prefixes = json_read('prefix')
    prefixes[str(guild.id)] = '?'
    json_write('prefix', prefixes)

#important DO NOT CHANGE
#Leaving the server and removing the prefix
@client.event
async def on_guild_remove(guild):
    prefixes = json_read('prefix')
    prefixes.pop(str(guild.id))
    json_write('prefix', prefixes)

#changes the prefix on command
@client.command()
@commands.has_guild_permissions(administrator=True)
@commands.guild_only()
async def changeprefix(ctx, prefix):
    """
    Command to change bot prefix
    """
    prefixes = json_read('prefix')
    prefixes[str(ctx.guild.id)] = prefix
    json_write('prefix', prefixes)
    await ctx.send(f'Prefix changed to {prefix}')

#music stuff
@client.command()
async def play (ctx, url:str):
    song = os.path.isfile("song.mp3")
    try:
        if song:
            os.remove("song.mp3")
    except PermissionError:
        await ctx.send("UWU")
        return

    channel = ctx.message.author.voice.channel
    voiceChannel = discord.utils.get(ctx.guild.voice_channels, name=channel.name)
    await voiceChannel.connect()
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            os.rename(file, "song.mp3")
    voice.play(discord.FFmpegPCMAudio("song.mp3"))

@client.command()
async def leave (ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    await voice.disconnect()


@client.command()
async def ping(ctx):
    """
    Test command to get latency
    """
    await ctx.send(f'{round(client.latency * 1000)}ms')





@client.command()
@commands.is_owner()
async def logout(ctx):
    await client.logout()

#important DO NOT CHANGE
#run
client.run(os.getenv("TOKEN"))
