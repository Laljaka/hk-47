import discord
import asyncio
from discord.ext import commands
from misc.embed import player_embed

from youtube_dl import YoutubeDL


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = {}
        self.is_stopping = {}

        self.music_queue = {}
        self.YDL_OPTIONS = {
            'format': 'bestaudio/best',
            'noplaylist': 'True',
            'cookiefile': 'cookies.txt',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}

        self.vc = {}

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
            except Exception:
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    async def play_next(self, ctx):
        if len(self.music_queue[ctx.guild.id]) > 0:
            self.is_playing[ctx.guild.id] = True

            m_url = self.music_queue[ctx.guild.id][0][0]['source']

            await ctx.send(embed=player_embed('Now playing:', self.music_queue[ctx.guild.id][0][0]['title'], discord.Colour.green()))
            self.music_queue[ctx.guild.id].pop(0)

            source = await discord.FFmpegOpusAudio.from_probe(m_url, **self.FFMPEG_OPTIONS)
            self.vc[ctx.guild.id].play(source, after=lambda e: print(
                'Player error: %s' % e) if e else self.bot.loop.create_task(self.play_next(ctx)))

        else:
            self.is_playing[ctx.guild.id] = False

    async def play_music(self, ctx):
        if len(self.music_queue[ctx.guild.id]) > 0:
            self.is_playing[ctx.guild.id] = True
            if ctx.guild.id not in self.vc:
                self.vc[ctx.guild.id] = ctx.voice_client

            m_url = self.music_queue[ctx.guild.id][0][0]['source']

            if self.vc[ctx.guild.id] is None or not self.vc[ctx.guild.id].is_connected():
                self.vc[ctx.guild.id] = await self.music_queue[ctx.guild.id][0][1].connect()
            else:
                await self.vc[ctx.guild.id].move_to(
                    self.music_queue[ctx.guild.id][0][1])

            await ctx.send(embed=player_embed('Now playing:', self.music_queue[ctx.guild.id][0][0]['title'], discord.Colour.green()))
            self.music_queue[ctx.guild.id].pop(0)

            source = await discord.FFmpegOpusAudio.from_probe(m_url, **self.FFMPEG_OPTIONS)
            self.vc[ctx.guild.id].play(source, after=lambda e: print(
                'Player error: %s' % e) if e else self.bot.loop.create_task(self.play_next(ctx)))
        else:
            self.is_playing[ctx.guild.id] = False

    @commands.command(aliases=['p'])
    @commands.guild_only()
    async def play(self, ctx, *args):
        query = " ".join(args)

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
                await ctx.send(embed=player_embed('Successfully queued:', song['title'], discord.Colour.gold()))
                self.music_queue[ctx.guild.id].append([song, voice_channel])

                if self.is_playing[ctx.guild.id] is False:
                    await self.play_music(ctx)

    @commands.command()
    @commands.guild_only()
    async def skip(self, ctx):
        if ctx.guild.id in self.vc:
            if self.vc[ctx.guild.id] is not None and self.vc[ctx.guild.id].is_connected():
                if self.is_playing[ctx.guild.id] is True:
                    self.vc[ctx.guild.id].stop()
                    await self.play_music(ctx)
                else:
                    await ctx.send("I'm not cuwently playing anywing owo")
            else:
                await ctx.send("I'm not even connected to a voice chat")

    @commands.command()
    @commands.guild_only()
    async def stop(self, ctx):
        if ctx.guild.id in self.vc:
            if self.vc[ctx.guild.id] is not None and self.vc[ctx.guild.id].is_connected():
                if self.is_playing[ctx.guild.id] is True:
                    self.vc[ctx.guild.id].stop()
                    self.is_playing[ctx.guild.id] = False
                    self.music_queue[ctx.guild.id].clear()
                else:
                    await ctx.send("I'm not cuwently playing anywing owo")
            else:
                await ctx.send("I'm not even connected to a voice chat")

    @commands.command()
    @commands.guild_only()
    async def leave(self, ctx):
        if ctx.guild.id in self.vc:
            if self.vc[ctx.guild.id] is not None and self.vc[ctx.guild.id].is_connected():
                if self.is_playing[ctx.guild.id] is True:
                    self.vc[ctx.guild.id].stop()
                    self.is_playing[ctx.guild.id] = False
                    self.music_queue[ctx.guild.id].clear()
                self.is_stopping[ctx.guild.id] = True
                await self.vc[ctx.guild.id].disconnect()
                await asyncio.sleep(1)
                self.is_stopping[ctx.guild.id] = False
            else:
                await ctx.send("I'm not even connected to a voice chat")

    @commands.command()
    @commands.guild_only()
    async def testing(self, ctx):
        await ctx.send(embed=player_embed('Title', 'Description', discord.Colour.green()))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # print(type(member))
        # print(member.id)
        # print(type(before))
        # print(type(before.channel))
        # print(type(after))
        # print(type(after.channel))
        # print(self.bot.user.id)
        if member.id == self.bot.user.id and after.channel is None:
            if self.is_stopping[member.guild.id] is True:
                pass
            else:
                await self.vc[member.guild.id].disconnect()
                self.vc[member.guild.id].stop()
                self.is_playing[member.guild.id] = False
                self.music_queue[member.guild.id].clear()
                print("forcefully kicked")
