import re
import discord
from discord.ext import commands, tasks
import lavalink
import asyncio

url_rx = re.compile(r'https?://(?:www\.)?.+')


class LavalinkMusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.lavalink = lavalink.Client(self.bot.user.id)
        self.bot.lavalink.add_node('localhost', 2333, 'testing', 'eu', 'music-node')
        self.bot.add_listener(self.bot.lavalink.voice_update_handler, 'on_socket_response')
        self.bot.lavalink.add_event_hook(self.track_hook)
        self._tasks = {}

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None

        if guild_check:
            await self.ensure_voice(ctx)

        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        # Create returns a player if one exists, otherwise creates.
        # This line is important because it ensures that a player always exists for a guild.

        # Most people might consider this a waste of resources for guilds that aren't playing, but this is
        # the easiest and simplest way of ensuring players are created.

        # These are commands that require the bot to join a voicechannel (i.e. initiating playback).
        # Commands such as volume/skip etc don't require the bot to be in a voicechannel so don't need listing here.
        should_connect = ctx.command.name in ('play_new',)

        if not ctx.author.voice or not ctx.author.voice.channel:
            # Our cog_command_error handler catches this and sends it to the voicechannel.
            # Exceptions allow us to "short-circuit" command invocation via checks so the
            # execution state of the command goes no further.
            raise commands.CommandInvokeError('Join a voicechannel first.')

        if not player.is_connected:
            if not should_connect:
                raise commands.CommandInvokeError('Not connected.')

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:  # Check user limit too?
                raise commands.CommandInvokeError('I need the `CONNECT` and `SPEAK` permissions.')

            player.store('channel', ctx.channel.id)
            await ctx.guild.change_voice_state(channel=ctx.author.voice.channel, self_mute=False, self_deaf=True)
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise commands.CommandInvokeError('You need to be in my voicechannel.')

    async def countdown(self, gid):
        print('commence')
        # self.vc[gid].stop()
        # self.is_stopping[ctx.guild.id] = True
        # await self.vc[ctx.guild.id].disconnect(force=True)
        # await asyncio.sleep(1)
        # self.is_stopping[ctx.guild.id] = False
        # await ctx.send('I left the voice chat due to inactivity')
        player = self.bot.lavalink.player_manager.get(gid)
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        # await player.stop()
        # Disconnect from the voice channel.
        guild = self.bot.get_guild(gid)
        cid = player.fetch('channel')
        channel = guild.get_channel(cid)
        await guild.change_voice_state(channel=None)
        await channel.send('*⃣ | I left the voice chat due to inactivity')
        self.cancel_task(gid)

    async def before_countdown(self):
        print('countdown has started')
        await asyncio.sleep(120)

    def task_launcher(self, gid):
        new_task = tasks.loop(seconds=20.0)(self.countdown)
        new_task.before_loop(self.before_countdown)
        new_task.start(gid)
        self._tasks[gid] = new_task

    def cancel_task(self, guild_id):
        if guild_id in self._tasks:
            if self._tasks[guild_id].is_running:
                self._tasks[guild_id].cancel()
                print('cancelled')

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild_id = int(event.player.guild_id)
            self.task_launcher(guild_id)
            # guild = self.bot.get_guild(guild_id)
            # await guild.change_voice_state(channel=None)
        if isinstance(event, lavalink.events.TrackEndEvent):
            print('track ends TODO')
        if isinstance(event, lavalink.events.NodeDisconnectedEvent):
            print('node disconnected')

    @commands.command(aliases=['p_new'])
    async def play_new(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        # Get the player for this guild from cache.
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        # Remove leading and trailing <>. <> may be used to suppress embedding links in Discord.
        query = query.strip('<>')

        # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
        # SoundCloud searching is possible by prefixing "scsearch:" instead.
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        # Results could be None if Lavalink returns an invalid response (non-JSON/non-200 (OK)).
        # ALternatively, resullts['tracks'] could be an empty array if the query yielded no tracks.
        if not results or not results['tracks']:
            return await ctx.send('Nothing found!')

        embed = discord.Embed(color=discord.Color.blurple())

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']

            for track in tracks:
                # Add all of the tracks from the playlist to the queue.
                player.add(requester=ctx.author.id, track=track)

            embed.title = 'Playlist Enqueued!'
            embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
        else:
            track = results['tracks'][0]
            embed.title = 'Track Enqueued'
            embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'

            # You can attach additional information to audiotracks through kwargs, however this involves
            # constructing the AudioTrack class yourself.
            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)

        await ctx.send(embed=embed)

        # We don't want to call .play() if the player is playing as that will effectively skip
        # the current track.
        if not player.is_playing:
            self.cancel_task(ctx.guild.id)
            await player.play()

    @commands.command()
    async def skip_new(self, ctx, pos=None):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send('Not connected.')
        # if not len(player.queue) > 0 and not player.is_playing:
        #     return await ctx.send('The queue is empty.')
        try:
            to_int = int(pos)
        except Exception:
            await player.stop()
            await player.skip()
        else:
            if len(player.queue) >= to_int > 1:
                player.queue.pop(to_int - 2)
            elif to_int == 1:
                await player.stop()
                await player.skip()
            else:
                await ctx.send('No song at stated position')

    @commands.command()
    async def queue_new(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send('Not connected.')
        if not len(player.queue) > 0:
            return await ctx.send('The queue is empty.')
        embed = discord.Embed(title='Queue:', color=discord.Color.gold())
        embed.add_field(name=f'{player.current.title}', value='in position 1 -- NOW PLAYING!', inline=False)
        for i, track in enumerate(player.queue):
            embed.add_field(name=f'{track.title}', value=f'in position {i + 2}', inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=['dc'])
    async def disconnect(self, ctx):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send('Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send('You\'re not in my voicechannel!')

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()
        # Disconnect from the voice channel.
        await ctx.guild.change_voice_state(channel=None)
        await ctx.send('*⃣ | Disconnected.')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id == self.bot.user.id and after.channel is None:
            player = self.bot.lavalink.player_manager.get(member.guild.id)
            # if self.is_stopping[member.guild.id] is True:
            #     pass
            # else:
            player.queue.clear()
            await player.stop()
            # await member.guild.change_voice_state(channel=None)
            # self.is_playing[member.guild.id] = False
            print("forcefully kicked")
