import discord
import json
from discord.ext import commands
import os
from dotenv import load_dotenv
import emojis
#from datetime import datetime
load_dotenv()

#Variables
intents = discord.Intents.default()
intents.members = True
restrictedTO = 798456032358694912

#stuff
def json_read(filename):
    with open(f'{filename}.json', 'r') as f:
        data = json.load(f)
    return data

def json_write(filename, data):
    with open(f'{filename}.json', 'w') as f:
        json.dump(data, f, indent =4)

def get_prefix(client, message):
    prefixes = json_read('prefix')
    return prefixes[str(message.guild.id)]


client = commands.Bot(command_prefix = get_prefix, intents = intents)

def check_roleassign_message(payload):
    roleassign1 = json_read('roleassign')
    return roleassign1[str(payload.guild_id)]['rolemessage']

#Ready check
@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.listening, name='the screams of meatbags'))
    print('Bot is ready as {0.user}'.format(client))

#Joining the server and creating a prefix in json file
@client.event
async def on_guild_join(guild):
    prefixes = json_read('prefix')
    prefixes[str(guild.id)] = '?'
    json_write('prefix', prefixes)

#Leaving the server and removing the prefix
@client.event
async def on_guild_remove(guild):
    prefixes = json_read('prefix')
    prefixes.pop(str(guild.id))
    json_write('prefix', prefixes)
    prefixes = json_read('roleassign')
    prefixes.pop(str(guild.id))
    json_write('roleassign', prefixes)

#------------------------------------------------------------------------------
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

#------------------------------------------------------------------------------
@client.group()
@commands.has_guild_permissions(administrator=True)
@commands.guild_only()
async def roleassign(ctx):
    """
    Command to specify roleassign message and emojis
    """
    if ctx.invoked_subcommand == None:
        prefix = get_prefix(ctx, ctx.message)
        await ctx.send(f'Invalid parameters passed, type {prefix}help roleassign to find more')

@roleassign.command()
async def create(message):
    """
    Command to create roleassign message
    """
    def check(msg):
        if msg.author.id == message.author.id:
            print('what the fuck')
            return True

    roleassign1 = json_read('roleassign')
    deletable = await message.channel.send('Please send the message')
    msgtorole = await client.wait_for('message', check=check)
    roleassign1[str(message.guild.id)] = {'rolemessage': msgtorole.id, 'emojis': []}
    json_write('roleassign', roleassign1)
    await message.message.delete()
    await deletable.delete()
    #await message.channel.purge(limit=6, check=chek2)

@roleassign.command()
async def add(message):
    """
    Command to add an emoji to roleassign message
    """
    def check(msg):
        if msg.author.id == message.author.id:
            print('what the fuck')
            return True
    deletable = await message.channel.send("Type the exact name of the role. Please note that there should also be an emoji with exact same name as the role")
    emojirolename = await client.wait_for('message', check=check)
    guild = client.get_guild(message.guild.id)
    emoji = discord.utils.get(guild.emojis, name=emojirolename.content)
    role = discord.utils.get(guild.roles, name=emojirolename.content)
    #print(emoji)
    #print(role)
    if emoji != None and role != None:
        roleassign = json_read('roleassign')
        roleassign[str(message.guild.id)]['emojis'].append(emoji.name)
        json_write('roleassign', roleassign)
        seek = await message.fetch_message(roleassign[str(message.guild.id)]['rolemessage'])
        await seek.add_reaction(emoji)
        await message.message.delete()
        await deletable.delete()
        await emojirolename.delete()
    else:
        await message.channel.send('There was an error, please try again')

#@client.command()
#async def dm(ctx):
    #user=await client.get_user_info("User's ID here")
#    await ctx.message.author.send("hallo")


@roleassign.command()
async def clear(message):
    """
    Command to clear emojis under roleassign message
    """
    roleassign1 = json_read('roleassign')
    roleassign1[str(message.guild.id)]['emojis'] = []
    json_write('roleassign', roleassign1)

@roleassign.command()
async def remove(message):
    """
    Command to remove roleassign message
    """
    roleassign1 = json_read('roleassign')
    roleassign1[str(message.guild.id)]['rolemessage'] = None
    roleassign1[str(message.guild.id)]['emojis'] = []
    json_write('roleassign', roleassign1)

@roleassign.command()
async def remove_exact(ctx, message):
    """
    Command to remove exact emoji from the list (must be used in the same chat as the original message)
    """
    roleassign1 = json_read('roleassign')
    if message in roleassign1[str(ctx.guild.id)]['emojis']:
        roleassign1[str(ctx.guild.id)]['emojis'].remove(message)
        seek = await ctx.fetch_message(roleassign1[str(ctx.guild.id)]['rolemessage'])
        json_write('roleassign', roleassign1)
        guild = client.get_guild(ctx.guild.id)
        emojiz = discord.utils.get(guild.emojis, name=message)
        for reaction in seek.reactions:
            #    if reaction.name == emojiz.name:                                   NEED TESTING
            #        outcome = reaction
            async for user in reaction.users(): # change reaction to outcome
                await seek.remove_reaction(emojiz, user)
    else:
        await ctx.author.send('There is no such emoji in the list, please check your spelling')

@remove_exact.error
async def infof(ctx, error):
    if isinstance(error, commands.errors.CommandInvokeError):
        await ctx.author.send('I could not find the message in the channel, please use this command in the same channel as the role message')
    else:
        print(error)

#discord.ext.commands.errors.CommandInvokeError: Command raised an exception: NotFound: 404 Not Found (error code: 10008): Unknown Message CommandInvokeError

@client.group()
@commands.has_guild_permissions(administrator=True)
@commands.guild_only()
async def insta(ctx):
    """
    Command to make a bot react to a message with a couple of emojis
    """
    if ctx.invoked_subcommand == None:
        prefix = get_prefix(ctx, ctx.message)
        await ctx.send(f'Invalid parameters passed, type {prefix}help insta to find more')

@insta.command()
async def react(ctx, *args):
    """
    Reply to a message while executing this command
    """
    roleassign1 = json_read('roleassign')
    if ctx.message.reference.message_id != roleassign1[str(ctx.guild.id)]['rolemessage']:
        seek = await ctx.fetch_message(ctx.message.reference.message_id)
        guild = client.get_guild(ctx.guild.id)
        for arg in args:
            emoji = discord.utils.get(guild.emojis, name=arg)
            if emoji != None:
                await seek.add_reaction(emoji)
            else:
                emoji = emojis.db.get_emoji_by_alias(arg)
                await seek.add_reaction(emoji.emoji)
        await ctx.message.delete()
    else:
        await ctx.author.send("You cheeky bastard, you can't do that")
        await ctx.message.delete()

@insta.command()
async def unreact(ctx):
    """
    Reply to a message while executing this command
    """
    roleassign1 = json_read('roleassign')
    if ctx.message.reference.message_id != roleassign1[str(ctx.guild.id)]['rolemessage']:
        seek = await ctx.fetch_message(ctx.message.reference.message_id)
        guild = client.get_guild(ctx.guild.id)
        member = guild.get_member(client.user.id)
        for reaction in seek.reactions:
            await seek.remove_reaction(reaction, member)
        await ctx.message.delete()
    else:
        await ctx.author.send("You cheeky bastard, you can't do that")
        await ctx.message.delete()

#------------------------------------------------------------------------------ ADD TO ANOTHER FILE
#Commands to add and remove roles by reacting to the message with emojis
@client.event
async def on_raw_reaction_add(payload):
    if payload.message_id == check_roleassign_message(payload) and payload.user_id != client.user.id:
        storage = json_read('roleassign')
        if payload.emoji.name in storage[str(payload.guild_id)]['emojis']:
            guild = client.get_guild(payload.guild_id) #guild = discord.utils.find(lambda g : g.id == payload.guild_id, client.guilds)
            role = discord.utils.get(guild.roles, name=payload.emoji.name) #role = guild.get_role(payload.emoji.name)
            member = guild.get_member(payload.user_id) #member = discord.utils.find(lambda m : m.id == payload.user_id, guild.members)
            #member = payload.member
            #role = guild.get_role(payload.emoji.name)
            #print(payload.member)
            print(guild)
            print(payload.user_id)
            print(member)
            await member.add_roles(role)
        else:
            channel = client.get_channel(payload.channel_id)
            seek = await channel.fetch_message(storage[str(payload.guild_id)]['rolemessage'])
            guild = client.get_guild(payload.guild_id)
            #emoji = payload.emoji#discord.utils.get(guild.emojis, name=payload.emoji.name)
            member = guild.get_member(payload.user_id)
            await seek.remove_reaction(payload.emoji, member)
    else:
        return

@client.event
async def on_raw_reaction_remove(payload):
    if payload.user_id != client.user.id:
        if payload.message_id == check_roleassign_message(payload):
            guild = client.get_guild(payload.guild_id)#discord.utils.find(lambda g : g.id == payload.guild_id, client.guilds)
            role = discord.utils.get(guild.roles, name=payload.emoji.name)#role = guild.get_role(payload.emoji.name)
            #member = discord.utils.find(lambda m : m.id == payload.user_id, guild.members)
            #member = payload.member
            #member = guild.get_member(payload.user_id)
            #role = guild.get_role(payload.emoji.name)
            member = guild.get_member(payload.user_id)
            print(guild)
            print(payload.user_id)
            print(member)
            await member.remove_roles(role)
        else:
            return

#------------------------------------------------------------------------------
@client.command()
async def ping(ctx):
    """
    Test command to get latency
    """
    await ctx.send(f'{round(client.latency * 1000)}ms')

@client.command()
@commands.has_guild_permissions(administrator=True)
@commands.guild_only()
async def purge(ctx, amount=100):
    """
    Command to clear messages (100 is default)
    """
    await ctx.channel.purge(limit=amount)

@client.command()
@commands.has_guild_permissions(administrator=True)
@commands.guild_only()
async def forceban(ctx, id, reason="Not specified", days=0):
    """
    Bans user if he is not on th server
    Usage: {prefix}forceban id reason(optional) days(how many messages to delete(optional))
    """
    await client.http.ban(id, ctx.guild.id, reason=reason, delete_message_days=days)
    await ctx.author.send(f"User <@{id}> has been banned")

@forceban.error
async def infog(ctx, error):
    if isinstance(error, discord.Forbidden):
        await ctx.author.send("Something went wrong")                                                           #prbs unneessary
    else:
        raise error

@client.command()
@commands.has_guild_permissions(administrator=True)
@commands.guild_only()
async def user_info_setup(ctx, channel: discord.TextChannel):
    channels = json_read('storage/channels')
    channels[str(ctx.guild.id)] = channel.id
    json_write('storage/channels', channels)

@user_info_setup.error
async def notfound(ctx, error):
    if isinstance(error, commands.errors.ChannelNotFound):
        await ctx.author.send("Please mention a channel.")
    else:
        raise error

#To do
@client.event
async def on_member_join(member):
    channel_raw = json_read('storage/channels')
    channel = member.guild.get_channel(channel_raw[str(member.guild.id)])
    if channel != None:
        #await channel.send(f"User <@{member.id}> joined the server.\nTheir account was created at {member.created_at}")                       #  NEED TESTING
        embed=discord.Embed(
        title="User joined",
        #url="https://realdrewdata.medium.com/",
        #description="Here are some ways to format text",
        color=discord.Color.green())
        #embed.set_author(name=f"{member.display_name}#{member.discriminator}", icon_url=f"{member.avatar_url}")
        #embed.set_author(name=ctx.author.display_name, url="https://twitter.com/RealDrewData", icon_url=ctx.author.avatar_url)
        #embed.set_thumbnail(url="https://i.imgur.com/axLm3p6.jpeg")
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="User name", value=f"{member.display_name}#{member.discriminator}", inline=False)
        embed.add_field(name="User link", value=f"{member.mention}", inline=False)
        embed.add_field(name="User id", value=f"{member.id}", inline=False)
        embed.add_field(name="Account created", value=f"{member.created_at.strftime('%d %b %Y at %H:%M')}", inline=False)
        #embed.set_footer(text="Learn more here: realdrewdata.medium.com")
        await channel.send(embed=embed)

@client.event
async def on_member_remove(member):
    channel_raw = json_read('storage/channels')
    channel = member.guild.get_channel(channel_raw[str(member.guild.id)])
    if channel != None:
        #await channel.send(f"User <@{member.id}> left the server")
        embed=discord.Embed(
        title="User left",
        color=discord.Color.red())
        #embed.set_author(name=f"{member.display_name}#{member.discriminator}", icon_url=f"{member.avatar_url}")
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="User name", value=f"{member.display_name}#{member.discriminator}", inline=False)
        embed.add_field(name="User link", value=f"{member.mention}", inline=False)
        embed.add_field(name="User id", value=f"{member.id}", inline=False)
        embed.add_field(name="Joined the server", value=f"{member.joined_at.strftime('%d %b %Y at %H:%M')}", inline=False)
        await channel.send(embed=embed)

@client.command()
@commands.is_owner()
async def info(ctx, member: discord.Member):
    datestring = member.created_at.strftime('%d %b %y %H:%M')
    print(datestring)



@client.command()
@commands.is_owner()
async def logout(ctx):
    await client.logout()

@client.command()
@commands.is_owner()
async def test(ctx):
#    roleassign1 = json_read('storage')
#    print(roleassign1[str(ctx.guild.id)]['emojis'])
     print(client.user.id)

#    await ctx.send('Plaese type password to change channel restriction')
#    msg = await client.wait_for('message')
#    print(msg.content)
#     guild = client.get_guild(ctx.guild.id)
#     print(guild.members)
#    if msg.content != password:
#        return
#    else:
#        global restrictedTO
#        restrictedTO = ctx.channel.id
#        print(restrictedTO)


#run
client.run(os.getenv("TOKEN"))
