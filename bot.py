import discord
import json
from discord.ext import commands
import os
from dotenv import load_dotenv
#import emojis
#from datetime import datetime
load_dotenv()

#Variables
intents = discord.Intents.default()
intents.members = True

#stuff
def json_read(filename):
    with open(f'storage/{filename}.json', 'r') as f:
        data = json.load(f)
    return data

def json_write(filename, data):
    with open(f'storage/{filename}.json', 'w') as f:
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
    await client.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.listening, name='the screams of meatbags'))
    print('Bot is ready as {0.user}'.format(client))

#Joining the server and creating a prefix in json file
@client.event
async def on_guild_join(guild):
    prefixes = json_read('prefix')
    prefixes[str(guild.id)] = '?'
    json_write('prefix', prefixes)
    prefixes = json_read('roleassign')
    prefixes[str(guild.id)] = {'rolemessage': None, 'emojis': []}
    json_write('roleassign', prefixes)
    prefixes = json_read('channels')
    prefixes[str(guild.id)] = None
    json_write('channels', prefixes)

#Leaving the server and removing the prefix
@client.event
async def on_guild_remove(guild):
    prefixes = json_read('prefix')
    prefixes.pop(str(guild.id))
    json_write('prefix', prefixes)
    prefixes = json_read('roleassign')
    prefixes.pop(str(guild.id))
    json_write('roleassign', prefixes)
    prefixes = json_read('channels')
    prefixes.pop(str(guild.id))
    json_write('channels', prefixes)

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
    roleassign1[str(message.guild.id)]['rolemessage'] = msgtorole.id
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
    await message.channel.send("Succesfully cleared list of emojis from the database")

@roleassign.command()
async def remove(message):
    """
    Command to remove roleassign message
    """
    roleassign1 = json_read('roleassign')
    roleassign1[str(message.guild.id)]['rolemessage'] = None
    roleassign1[str(message.guild.id)]['emojis'] = []
    json_write('roleassign', roleassign1)
    await message.channel.send("Succesfully removed roleassign message from the database")

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
            await seek.add_reaction(arg)
        await ctx.message.delete()
    else:
        await ctx.author.send("Please do not mix this command with roleassign related message")
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
        await ctx.author.send("Please do not mix this command with roleassign related message")
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
            await member.add_roles(role)
            print(f"DEV:    on_raw_reaction_add:    Succesfully added role {role.name} to user {member.display_name} on the server {guild.name}")
        else:
            channel = client.get_channel(payload.channel_id)
            seek = await channel.fetch_message(storage[str(payload.guild_id)]['rolemessage'])
            guild = client.get_guild(payload.guild_id)
            #emoji = payload.emoji#discord.utils.get(guild.emojis, name=payload.emoji.name)
            member = guild.get_member(payload.user_id)
            await seek.remove_reaction(payload.emoji, member)
            print(f"DEV:    on_raw_reaction_add:    User {member.display_name} tried adding {payload.emoji.name} on the server {guild.name} which was not allowed under this message")
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
            await member.remove_roles(role)
            print(f"DEV:    on_raw_reaction_remove:    Succesfully removed role {role.name} from user {member.display_name} on the server {guild.name}")
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
    def check(reaction, user):
        if user == ctx.author:
            if reaction.emoji == u'\U0001F7E2' or reaction.emoji == u'\U0001F534':
                return True

    if amount > 20:
        target = await ctx.channel.send(f"Are you sure you want to delete {amount} messages?")
        await target.add_reaction('\U0001F7E2')
        await target.add_reaction('\U0001F534')
        reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
        if reaction.emoji == '\U0001F7E2':
            await ctx.channel.purge(limit=amount+2)
        if reaction.emoji == '\U0001F534':
            return
    else:
        await ctx.channel.purge(limit=amount+1)

@client.command()
@commands.has_guild_permissions(administrator=True)
@commands.guild_only()
async def forceban(ctx, reason="Not specified", *ids):
    """
    Bans user if he is not on the server
    Usage: {prefix}forceban "reason"(optional) id, id, id etc...
    """
    for id in ids:
        await client.http.ban(id, ctx.guild.id, reason=reason, delete_message_days=0)
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
    channels = json_read('channels')
    channels[str(ctx.guild.id)] = channel.id
    json_write('channels', channels)

@user_info_setup.error
async def notfound(ctx, error):
    if isinstance(error, commands.errors.ChannelNotFound):
        await ctx.author.send("Please mention a channel.")
    else:
        raise error

#To do
@client.event
async def on_member_join(member):
    channel_raw = json_read('channels')
    guild = client.get_guild(member.guild.id)
    if guild == None:
        print(f"DEV:    on_member_join:    Member {member.display_name} joined and it's guild was not found by it's id: {member.guild.id}")
    else:
        channel = guild.get_channel(channel_raw[str(member.guild.id)])
        if channel == None:
            print(f"DEV:    on_member_join:    Member {member.display_name} joined the guild {guild.name} Channel wasn't found in json")
        else:
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
            #embed.add_field(name="User link", value=f"{member.mention}", inline=True)
            embed.add_field(name="User id", value=f"{member.id}", inline=False)
            embed.add_field(name="Account created", value=f"{member.created_at.strftime('%d %b %Y at %H:%M')}", inline=False)
            #embed.set_footer(text="Learn more here: realdrewdata.medium.com")
            await channel.send(embed=embed)

@client.event
async def on_member_remove(member):
    channel_raw = json_read('channels')
    guild = client.get_guild(member.guild.id)
    if guild == None:
        print(f"DEV:    on_member_remove:     Member {member.display_name} left and it's guild was not found by it's id: {member.guild.id}")
    else:
        channel = guild.get_channel(channel_raw[str(member.guild.id)])
        if channel == None:
            print(f"DEV:    on_member_remove:     Member {member.display_name} joined the guild {guild.name} Channel wasn't found in json")
        else:
            #await channel.send(f"User <@{member.id}> left the server")
            embed=discord.Embed(
            title="User left",
            color=discord.Color.red())
            #embed.set_author(name=f"{member.display_name}#{member.discriminator}", icon_url=f"{member.avatar_url}")
            embed.set_thumbnail(url=member.avatar_url)
            embed.add_field(name="User name", value=f"{member.display_name}#{member.discriminator}", inline=False)
            #embed.add_field(name="User link", value=f"{member.mention}", inline=True)
            embed.add_field(name="User id", value=f"{member.id}", inline=False)
            embed.add_field(name="Joined the server", value=f"{member.joined_at.strftime('%d %b %Y at %H:%M')}", inline=False)
            await channel.send(embed=embed)

@client.command()
@commands.is_owner()
async def eval(ctx, *, cmd=None):
    try:
        exec(cmd)
    except Exception as e:
        print(e.args)
    else:
        await ctx.message.add_reaction('\U0001F7E2')
        #ctx.author.send(f"```Python\n{e[0][0]['code'] + e[0][0]['message']}\n```")
    #await ctx.channel.send("👍")



@client.command()
@commands.is_owner()
async def logout(ctx):
    await client.logout()

@client.command()
@commands.is_owner()
async def test(ctx):
#    roleassign1 = json_read('storage')
#    print(roleassign1[str(ctx.guild.id)]['emojis'])
    res = await client.http.get_guild(647080905445212161)
    print(res)

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
