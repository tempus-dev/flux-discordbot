import discord
from discord.ext import commands


class Guidance(commands.Cog, name="Guidance"):
    """This cog contains all commands related to helping the user use Flux."""

    def __init__(self):
        pass

    @commands.command()
    async def help(self, ctx):
        """Helps the user with Flux commands"""
        pass


def setup(bot):
    bot.add_cog(Guidance())
