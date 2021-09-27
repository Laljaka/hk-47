import discord
import asyncio
from discord.ext import commands, tasks
from misc.embed import player_embed
from requests import get

from youtube_dl import YoutubeDL

from misc.parser import *


class music_cog(commands.Cog, name='Music control'):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = {}
        self.is_stopping = {}

        self.music_queue = {}
        self.YDL_OPTIONS = {
            'format': 'bestaudio/best',
            'noplaylist': 'True',
            'cookiefile': 'misc/cookies.txt',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}

        self.vc = {}
        self._tasks = {}

    async def countdown(self, ctx):
        print('commence')
        self.vc[ctx.guild.id].stop()
        self.is_stopping[ctx.guild.id] = True
        await self.vc[ctx.guild.id].disconnect(force=True)
        await asyncio.sleep(1)
        self.is_stopping[ctx.guild.id] = False
        await ctx.send('I left the voice chat due to inactivity')
        self._tasks[ctx.guild.id].cancel()

    async def before_countdown(self):
        print('countdown has started')
        await asyncio.sleep(120)

    def task_launcher(self, ctx):
        new_task = tasks.loop(seconds=20.0)(self.countdown)
        new_task.before_loop(self.before_countdown)
        new_task.start(ctx)
        self._tasks[ctx.guild.id] = new_task

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                get(item)
            except Exception:
                try:
                    info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
                except Exception:
                    return False
            else:
                testable = parse_check(item)
                if testable is not None:
                    try:
                        info = ydl.extract_info(f"ytsearch:{testable}", download=False)['entries'][0]
                    except Exception:
                        return False
                else:
                    try:
                        info = ydl.extract_info(item, download=False)
                    except Exception:
                        return False

        return {'source': info['formats'][0]['url'], 'title': info['title'], 'thumbnail': info['thumbnail']}

    async def play_next(self, ctx):
        print('play_next run')
        if len(self.music_queue[ctx.guild.id]) > 0:
            self.music_queue[ctx.guild.id].pop(0)
        if len(self.music_queue[ctx.guild.id]) > 0:
            self.is_playing[ctx.guild.id] = True
            if ctx.guild.id in self._tasks:
                if self._tasks[ctx.guild.id].is_running():
                    self._tasks[ctx.guild.id].cancel()

            m_url = self.music_queue[ctx.guild.id][0][0]['source']
            title = self.music_queue[ctx.guild.id][0][0]['title']
            thumb = self.music_queue[ctx.guild.id][0][0]['thumbnail']

            source = await discord.FFmpegOpusAudio.from_probe(m_url, **self.FFMPEG_OPTIONS)
            self.vc[ctx.guild.id].play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
            await ctx.send(embed=player_embed('Now playing:', title, ' ', discord.Colour.green(), thumb))

        else:
            self.is_playing[ctx.guild.id] = False
            if self.vc[ctx.guild.id].is_connected():
                self.task_launcher(ctx)

    async def play_music(self, ctx):
        print('play_music run')
        if len(self.music_queue[ctx.guild.id]) > 0:
            self.is_playing[ctx.guild.id] = True
            if ctx.guild.id in self._tasks:
                if self._tasks[ctx.guild.id].is_running():
                    self._tasks[ctx.guild.id].cancel()
            if ctx.guild.id not in self.vc:
                self.vc[ctx.guild.id] = ctx.voice_client

            m_url = self.music_queue[ctx.guild.id][0][0]['source']
            title = self.music_queue[ctx.guild.id][0][0]['title']
            thumb = self.music_queue[ctx.guild.id][0][0]['thumbnail']

            print(ctx.voice_client)

            #self.vc[ctx.guild.id] = await ctx.guild.change_voice_state(channel=self.music_queue[ctx.guild.id][0][1], self_mute=False, self_deaf=True)
            if self.vc[ctx.guild.id] is None or not self.vc[ctx.guild.id].is_connected():
                #if ctx.voice_client is not None:
                    #await self.vc[ctx.guild.id].move_to(
                        #self.music_queue[ctx.guild.id][0][1])
                #else:
                self.vc[ctx.guild.id] = await self.music_queue[ctx.guild.id][0][1].connect()
            else:
                await self.vc[ctx.guild.id].move_to(
                    self.music_queue[ctx.guild.id][0][1])

            source = await discord.FFmpegOpusAudio.from_probe(m_url, **self.FFMPEG_OPTIONS)
            self.vc[ctx.guild.id].play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
            await ctx.send(embed=player_embed('Now playing:', title, ' ', discord.Colour.green(), thumb))
        else:
            self.is_playing[ctx.guild.id] = False
            if self.vc[ctx.guild.id].is_connected():
                self.task_launcher(ctx)

    @commands.command(aliases=['p'], brief='Starts playing music and adds a track to the queue')
    @commands.guild_only()
    async def play(self, ctx, *link_or_song_name):
        """
        Starts playing music and adds a track to the queue, you can use either a link or a name of the song
        """
        print('play run')
        query = " ".join(link_or_song_name)

        if ctx.guild.id not in self.music_queue:
            self.music_queue[ctx.guild.id] = []

        if ctx.guild.id not in self.is_playing:
            self.is_playing[ctx.guild.id] = False

        if ctx.guild.id not in self.is_stopping:
            self.is_stopping[ctx.guild.id] = False

        # None type has no attribute channel if author of the message is not in vc
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("Connect to a voice channel first, silly")
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("Incorrect type")
            else:
                self.music_queue[ctx.guild.id].append([song, voice_channel])
                entry = len(self.music_queue[ctx.guild.id])
                #if self.is_playing[ctx.guild.id]:
                #    entry = entry + 1
                await ctx.send(embed=player_embed('Successfully queued:', song['title'], f'in position {entry}',
                                                  discord.Colour.gold(), song['thumbnail']))
                if self.is_playing[ctx.guild.id] is False:
                    await self.play_music(ctx)

    @commands.command()
    @commands.guild_only()
    async def skip(self, ctx, position=None):
        """
        Skips current song
        """
        if ctx.guild.id in self.vc:
            if self.vc[ctx.guild.id] is not None and self.vc[ctx.guild.id].is_connected():
                if self.is_playing[ctx.guild.id] is True:
                    try:
                        toint = int(position)
                    except Exception:
                        self.vc[ctx.guild.id].stop()
                    else:
                        if len(self.music_queue[ctx.guild.id]) >= toint > 1:
                            self.music_queue[ctx.guild.id].pop(toint - 1)
                        elif toint == 1:
                            self.vc[ctx.guild.id].stop()
                        else:
                            await ctx.send('No song at stated position')
                else:
                    await ctx.send("I'm not cuwently playing anywing owo")
            else:
                await ctx.send("I'm not even connected to a voice chat")

    @commands.command()
    @commands.guild_only()
    async def queue(self, ctx):
        """
        Displays the queue
        """
        if ctx.guild.id in self.vc:
            if self.vc[ctx.guild.id] is not None and self.vc[ctx.guild.id].is_connected():
                if self.is_playing[ctx.guild.id] is True:
                    embed = player_embed(None, 'Queue:', ' ', discord.Colour.blue(), None)
                    for iteration, entry in enumerate(self.music_queue[ctx.guild.id]):
                        if iteration == 0:
                            embed.add_field(name=entry[0]['title'], value=f'in position {iteration+1} -- NOW PLAYING!', inline=False)
                        else:
                            embed.add_field(name=entry[0]['title'], value=f'in position {iteration+1}', inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("I'm not cuwently playing anywing owo")
            else:
                await ctx.send("I'm not even connected to a voice chat")

    @commands.command()
    @commands.guild_only()
    async def stop(self, ctx):
        """
        Stops playing and purges the queue
        """
        if ctx.guild.id in self.vc:
            if self.vc[ctx.guild.id] is not None and self.vc[ctx.guild.id].is_connected():
                if self.is_playing[ctx.guild.id] is True:
                    self.is_playing[ctx.guild.id] = False
                    self.music_queue[ctx.guild.id].clear()
                    self.vc[ctx.guild.id].stop()
                else:
                    await ctx.send("I'm not cuwently playing anywing owo")
            else:
                await ctx.send("I'm not even connected to a voice chat")

    @commands.command(aliases=['l'])
    @commands.guild_only()
    async def leave(self, ctx):
        """
        Leaves the voice chat and purges the queue
        """
        if ctx.guild.id in self.vc:
            if self.vc[ctx.guild.id] is not None and self.vc[ctx.guild.id].is_connected():
                if self.is_playing[ctx.guild.id] is True:
                    self.music_queue[ctx.guild.id].clear()
                    self.vc[ctx.guild.id].stop()
                    self.is_playing[ctx.guild.id] = False
                self.is_stopping[ctx.guild.id] = True
                await self.vc[ctx.guild.id].disconnect(force=True)
                await asyncio.sleep(1)
                self.is_stopping[ctx.guild.id] = False
                if ctx.guild.id in self._tasks:
                    self._tasks[ctx.guild.id].cancel()
                await ctx.send(embed=player_embed(None, 'Successfully left the voice chat', 'TBR', discord.Colour.red(), None))
            else:
                await ctx.send("I'm not even connected to a voice chat")

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def testing(self, ctx, msg=None):
        await ctx.send('placeholder')

    # @commands.Cog.listener()
    # async def on_voice_state_update(self, member, before, after):
    #     if member.id == self.bot.user.id and after.channel is None:
    #         if self.is_stopping[member.guild.id] is True:
    #             pass
    #         else:
    #             await self.vc[member.guild.id].disconnect(force=True)
    #             self.music_queue[member.guild.id].clear()  # NEW
    #             self.vc[member.guild.id].stop()
    #             self.is_playing[member.guild.id] = False
    #             print("forcefully kicked")

