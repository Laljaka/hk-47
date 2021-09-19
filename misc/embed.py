import discord


def player_embed(author, title, desc, colour, thumb):
    embed = discord.Embed(
        title=title,
        description=desc,
        colour=colour,
    )

    embed.set_author(name=author)
    if thumb is not None:
        embed.set_thumbnail(url=thumb)

    return embed
