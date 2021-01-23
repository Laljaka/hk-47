import discord
import json
from discord.ext import commands
import os
from dotenv import load_dotenv
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
    prefixes = json_read('storage')
    return prefixes[str(message.guild.id)]['prefix']


client = commands.Bot(command_prefix = get_prefix, intents = intents)

def check_roleassign_message(payload):
    roleassign1 = json_read('storage')
    return roleassign1[str(payload.guild_id)]['rolemessage']

#Ready check
@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.listening, name='the screams of meatbags'))
    print('Bot is ready as {0.user}'.format(client))

#Joining the server and creating a storage in json file
@client.event
async def on_guild_join(guild):
    prefixes = json_read('storage')
    prefixes[str(guild.id)] = {'prefix': '?', 'rolemessage': None, 'emojis': []}
    json_write('storage', prefixes)

#Leaving the server and removing the storage
@client.event
async def on_guild_remove(guild):
    prefixes = json_read('storage')
    prefixes.pop(str(guild.id))
    json_write('storage', prefixes)

#------------------------------------------------------------------------------
@client.command()
@commands.has_guild_permissions(administrator=True)
@commands.guild_only()
async def changeprefix(ctx, prefix):
    """
    Command to change bot prefix
    """
    if ctx.channel.id != restrictedTO:
        return
    else:
        prefixes = json_read('storage')
        prefixes[str(ctx.guild.id)]['prefix'] = prefix
        json_write('storage', prefixes)
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

    roleassign1 = json_read('storage')
    deletable = await message.channel.send('Please send the message')
    msgtorole = await client.wait_for('message', check=check)
    roleassign1[str(message.guild.id)]['rolemessage'] = msgtorole.id
    json_write('storage', roleassign1)
    await message.message.delete()
    await deletable.delete()
    #await message.channel.purge(limit=6, check=chek2)

@roleassign.command()
async def add(message):
    """
    Command to add an emoji to roleassign message
    """
    def check(msg):
        if msg.author.id == message.author.id and msg.channel.id == message.channel.id:
            return True
    deletable = await message.channel.send("Type the exact name of the role. Please note that there should also be an emoji with exact same name as the role")
    emojirolename = await client.wait_for('message', check=check)
    guild = client.get_guild(message.guild.id)
    emoji = discord.utils.get(guild.emojis, name=emojirolename.content)
    role = discord.utils.get(guild.roles, name=emojirolename.content)
    #print(emoji)
    #print(role)
    if emoji != None and role != None:
        roleassign = json_read('storage')
        roleassign[str(message.guild.id)]['emojis'].append(emoji.name)
        json_write('storage', roleassign)
        seek = await message.fetch_message(roleassign[str(message.guild.id)]['rolemessage'])
        await seek.add_reaction(emoji)
        await message.message.delete()
        await deletable.delete()
        await emojirolename.delete()
    else:
        await message.channel.send('There was an error, please try again')


@roleassign.command()
async def clear(message):
    """
    Command to clear emojis under roleassign message
    """
    roleassign1 = json_read('storage')
    roleassign1[str(message.guild.id)]['emojis'] = []
    json_write('storage', roleassign1)

@roleassign.command()
async def remove(message):
    """
    Command to remove roleassign message
    """
    roleassign1 = json_read('storage')
    roleassign1[str(message.guild.id)]['rolemessage'] = None
    roleassign1[str(message.guild.id)]['emojis'] = []
    json_write('storage', roleassign1)

#------------------------------------------------------------------------------ ADD TO ANOTHER FILE
#Commands to add and remove roles by reacting to the message with emojis
@client.event
async def on_raw_reaction_add(payload):
    if payload.message_id == check_roleassign_message(payload) and payload.user_id != client.user.id:
        storage = json_read('storage')
        if payload.emoji.name in storage[str(payload.guild_id)]['emojis']:
            guild = client.get_guild(payload.guild_id)#guild = discord.utils.find(lambda g : g.id == payload.guild_id, client.guilds)
            role = discord.utils.get(guild.roles, name=payload.emoji.name)#role = guild.get_role(payload.emoji.name)
            member = guild.get_member(payload.user_id)#member = discord.utils.find(lambda m : m.id == payload.user_id, guild.members)
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
@commands.has_guild_permissions(manage_messages=True)
@commands.guild_only()
async def purge(ctx, amount=100):
    """
    Command to clear messages (100 is default)
    """
    def check(msg):
        if msg.id == ctx.message.id:
            return False
        else:
            return True
    await ctx.channel.purge(limit=amount, check=check)

#To do

@client.group()
async def request(ctx):
    """
    Command to manage the requests to get a role
    """
    prefix = get_prefix(ctx, ctx.message)
    if ctx.invoked_subcommand == None:
        await ctx.send(f'Invalid parameters passed, type {prefix}help roleassign to find more')

@request.command()
async def create(ctx):
    """
    Command to add a request to assign a role
    """
    def check(msg):
        if msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id:
            return True
    target_message = json_read('rolerequest')
    guild = client.get_guild(ctx.guild.id)
    await ctx.send("Please enter the message that will be used as request")
    rolemsg = await client.wait_for('message', check=check)
    target_message[str(guild.id)]['message_request'] = rolemsg.id
    target_message[str(guild.id)]['emoji_request'] = []
    json_write('rolerequest', target_message)

@request.command()
async def add(ctx):
    """
    Command to add an emoji to rolerequest message
    """
    def check(msg):
        if msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id:
            return True
    deletable = await message.channel.send("Type the exact name of the role. Please note that there should also be an emoji with exact same name as the role")
    emojirolename = await client.wait_for('message', check=check)
    guild = client.get_guild(ctx.guild.id)
    emoji = discord.utils.get(guild.emojis, name=emojirolename.content)
    role = discord.utils.get(guild.roles, name=emojirolename.content)
    #print(emoji)
    #print(role)
    if emoji != None and role != None:
        roleassign = json_read('rolerequest')
        roleassign[str(ctx.guild.id)]['emoji_request'].append(emoji.name)
        json_write('rolerequest', roleassign)
        seek = await message.fetch_message(roleassign[str(ctx.guild.id)]['rolemessage'])
        await seek.add_reaction(emoji)
        await message.message.delete()
        await deletable.delete()
        await emojirolename.delete()
    else:
        await message.channel.send('There was an error, please try again')

@client.command()
@commands.is_owner()
async def presence(ctx, status: discord.Status, activity):
    '''
    status, ActivityType.activity, presence message
    '''
    temp={
    "watching": discord.ActivityType.watching,
    "listening": discord.ActivityType.listening,
    "playing": discord.ActivityType.playing
    }
    message = await client.wait_for('message')
    await client.change_presence(status=status, activity=discord.Activity(type=temp[activity], name=message.content))
    #print(discord.Status.online)
    #print(discord.ActivityType.listening)

@presence.error
async def presence_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.author.send("you fucking idiot")
    else:
        raise error

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
