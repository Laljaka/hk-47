import discord
from discord.ext import commands

from youtube_dl import YoutubeDL

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = {}

        self.music_queue = {}
        self.YDL_OPTIONS = {
            'format': 'bestaudio',
            'noplaylist': 'True',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = {}

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
            except Exception:
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self, ctx):
        if len(self.music_queue[ctx.guild.id]) > 0:
            self.is_playing[ctx.guild.id] = True

            m_url = self.music_queue[ctx.guild.id][0][0]['source']

            self.music_queue[ctx.guild.id].pop(0)

            self.vc[ctx.guild.id].play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
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
                await self.vc[ctx.guild.id].move_to(self.music_queue[ctx.guild.id][0][1])#self.bot.move_to(self.music_queue[0][1])

            self.music_queue[ctx.guild.id].pop(0)

            self.vc[ctx.guild.id].play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            self.is_playing[ctx.guild.id] = False

    @commands.command()
    async def play(self, ctx, *args):
        query = " ".join(args)

        if ctx.guild.id not in self.music_queue:
            self.music_queue[ctx.guild.id] = []

        if ctx.guild.id not in self.is_playing:
            self.is_playing[ctx.guild.id] = False


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
        if self.vc[ctx.guild.id] is not None:
            self.vc[ctx.guild.id].stop()
            await self.play_music(ctx)