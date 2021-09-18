import discord


def player_embed(title, desc, colour):
    embed = discord.Embed(
        title=title,
        description=desc,
        colour=colour
    )

    return embed
