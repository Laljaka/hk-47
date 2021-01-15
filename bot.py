import discord
import json
from discord.ext import commands
import os
from dotenv import load_dotenv
load_dotenv()

#------------------------------------------------------------------------------
#Variables
intents = discord.Intents.default()
intents.members = True
restrictedTO = 798456032358694912

#------------------------------------------------------------------------------
#stuff

def json_read(filename):
    with open(f'{filename}.json', 'r') as f:
        data = json.load(f)
    return data

def json_write(filename, data):
    with open(f'{filename}.json', 'w') as f:
        json.dump(data, f, indent =4)

def get_prefix(client, message):
  #with open('storage.json', 'r') as f:
    #prefixes = json.load(f)
    prefixes = json_read('storage')
    return prefixes[str(message.guild.id)]['prefix']


client = commands.Bot(command_prefix = get_prefix, intents = intents)

def check_roleassign_message(payload):
    #with open('storage.json', 'r') as f:
    roleassign1 = json_read('storage')
    return roleassign1[str(payload.guild_id)]['rolemessage']

#------------------------------------------------------------------------------
#Ready check

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.listening, name='the screams of meatbags'))
    print('Bot is ready as {0.user}'.format(client))

#------------------------------------------------------------------------------
#Joining the server and creating a storage in json file
@client.event
async def on_guild_join(guild):
    #with open('storage.json', 'r') as f:
    prefixes = json_read('storage')

    prefixes[str(guild.id)] = {'prefix': '?', 'rolemessage': None, 'emojis': []}


    #with open('storage.json', 'w') as f:
    json_write('storage', prefixes)

#------------------------------------------------------------------------------
#Leaving the server and removing the storage

@client.event
async def on_guild_remove(guild):
    #with open('storage.json', 'r') as f:
    prefixes = json_read('storage')

    prefixes.pop(str(guild.id))

    #with open('storage.json', 'w') as f:
    json_write('storage', prefixes)

#------------------------------------------------------------------------------
@client.command()
@commands.has_guild_permissions(administrator=True)
async def changeprefix(ctx, prefix):
    """
    Command to change bot prefix
    """
    if ctx.channel.id != restrictedTO:
        return
    else:
        #with open('storage.json', 'r') as f:
        prefixes = json_read('storage')

        prefixes[str(ctx.guild.id)]['prefix'] = prefix

        #with open('storage.json', 'w') as f:
        json_write('storage', prefixes)

        await ctx.send(f'Prefix changed to {prefix}')

#------------------------------------------------------------------------------
@client.group()
@commands.has_guild_permissions(manage_roles=True)
async def roleassign(ctx):
    """
    Command to specify roleassign message and emojis
    """
    if ctx.invoked_subcommand == None:
        await ctx.send('Invalid parameters passed, type (PREFIX)help roleassign to find more')

@roleassign.command()
async def add(message):
    """
    Command to add roleassign message
    """
    if message.channel.id != restrictedTO:
        return
    else:
      
        def check(msg):
            if msg.author.id == message.author.id and msg.channel.id == restrictedTO:
                print('what the fuck')
                return True

        roleassign1 = json_read('storage')



        await message.channel.send('Please specify the amount of emojis to roles you want to have')

        num = await client.wait_for('message', check=check)

        roleassign1[str(message.guild.id)]['emojis'] = [''] * int(num.content)

        print(roleassign1[str(message.guild.id)]['emojis'])


        await message.channel.send('Please send the message')

        msgtorole = await client.wait_for('message', check=check)

        #with open('storage.json', 'r') as f:


        roleassign1[str(message.guild.id)]['rolemessage'] = msgtorole.id


        await message.channel.send('Now please react with emojis you want to be associated with roles under your message, please note that amount of emojis should be the same as you just specified')

        i=0
        for run in roleassign1[str(message.guild.id)]['emojis']:
            reaction = await client.wait_for('reaction_add')#ADD CHECK
            roleassign1[str(message.guild.id)]['emojis'][i] = reaction[0].emoji.name
            i=i+1

        def chek2(msg2):
            if msg2.id == msgtorole.id: 
                return False
            else:
                return True
        #with open('storage.json', 'w') as f:
        #json.dump(roleassign1, f, indent=4)
        json_write('storage', roleassign1)
        await message.channel.purge(limit=6, check=chek2)

@roleassign.command()
async def remove(message):
    """
    Command to remove roleassign message
    """
    if message.channel.id != restrictedTO:
        return
    else:
        roleassign1 = json_read('storage')
        roleassign1[str(message.guild.id)]['rolemessage'] = None
        roleassign1[str(message.guild.id)]['emojis'] = []
        json_write('storage', roleassign1)

#------------------------------------------------------------------------------
#Commands to add and remove roles by reacting to the message with emojis

@client.event
async def on_raw_reaction_add(payload):
    if payload.channel_id != restrictedTO:
        return
    else:
        if payload.message_id != check_roleassign_message(payload):
            return
        else:
            guild = client.get_guild(payload.guild_id)#guild = discord.utils.find(lambda g : g.id == payload.guild_id, client.guilds)
            role = discord.utils.get(guild.roles, name=payload.emoji.name)#role = guild.get_role(payload.emoji.name)
            member = guild.get_member(payload.user_id)#member = discord.utils.find(lambda m : m.id == payload.user_id, guild.members)
            #member = payload.member
            #role = guild.get_role(payload.emoji.name)
            #print(payload.member)
            print(guild)
            print(role)
            print(member)
            await member.add_roles(role)

@client.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id != restrictedTO:
        return
    else:
        if payload.message_id != check_roleassign_message(payload):
            return
        else:
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

#------------------------------------------------------------------------------
@client.command()
async def ping(ctx):
    """
    Test command
    """
    if ctx.channel.id != restrictedTO:
        return
    else:
        await ctx.send(f'{round(client.latency * 1000)}ms')

#------------------------------------------------------------------------------
@client.command()
@commands.has_guild_permissions(manage_messages=True)
async def purge(ctx, amount=100):
    """
    Command to clean the messages
    """
    if ctx.channel.id != restrictedTO:
        return
    else:
        def check(msg):
            if msg.id == ctx.message.id:
                return False
            else:
                return True
        await ctx.channel.purge(limit=amount, check=check)

#------------------------------------------------------------------------------
#To do

@client.command()
async def restrict(ctx):
#    await ctx.send('Plaese type password to change channel restriction')
#    msg = await client.wait_for('message')
#    print(msg.content)
     print(ctx.channel.id)
#    if msg.content != password:
#        return
#    else:
#        global restrictedTO
#        restrictedTO = ctx.channel.id
#        print(restrictedTO)

#------------------------------------------------------------------------------
#run
client.run(os.getenv("TOKEN"))
