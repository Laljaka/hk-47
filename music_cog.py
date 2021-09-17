import discord
from discord.ext import commands

from youtube_dl import YoutubeDL


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = {}
        # self.is_stopping = {}

        self.music_queue = {}
        self.YDL_OPTIONS = {
            'format': 'bestaudio/best',
            'noplaylist': 'True',
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

            self.music_queue[ctx.guild.id].pop(0)

            source = await discord.FFmpegOpusAudio.from_probe(m_url, **self.FFMPEG_OPTIONS)
            self.vc[ctx.guild.id].play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))

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

            self.music_queue[ctx.guild.id].pop(0)

            source = await discord.FFmpegOpusAudio.from_probe(m_url, **self.FFMPEG_OPTIONS)
            self.vc[ctx.guild.id].play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
        else:
            self.is_playing[ctx.guild.id] = False

    @commands.command(aliases=['p'])
    async def play(self, ctx, *args):
        query = " ".join(args)

        if ctx.guild.id not in self.music_queue:
            self.music_queue[ctx.guild.id] = []

        if ctx.guild.id not in self.is_playing:
            self.is_playing[ctx.guild.id] = False

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

                if self.is_playing[ctx.guild.id] is False:
                    await self.play_music(ctx)

    @commands.command()
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
    async def leave(self, ctx):
        if ctx.guild.id in self.vc:
            if self.vc[ctx.guild.id] is not None and self.vc[ctx.guild.id].is_connected():
                # if self.is_playing[ctx.guild.id] is True:
                # self.vc[ctx.guild.id].stop()
                # self.is_playing[ctx.guild.id] = False
                # self.music_queue[ctx.guild.id].clear()
                await self.vc[ctx.guild.id].disconnect()
            else:
                await ctx.send("I'm not even connected to a voice chat")

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
            await self.vc[member.guild.id].disconnect()
            self.vc[member.guild.id].stop()
            self.is_playing[member.guild.id] = False
            self.music_queue[member.guild.id].clear()
            print("forcefully kicked")
