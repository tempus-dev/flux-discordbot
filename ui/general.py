import time

import discord
from discord.ext import commands


class General(commands.Cog, name="General"):
    """This cog contains some general commands to assist in the usage of Flux."""

    def __init__(self):
        pass

    @commands.command()
    async def info(self, ctx) -> discord.Message:
        """Helps the user with Flux commands"""
        pass

    @commands.command()
    async def ping(self, ctx) -> discord.Message:
        before = time.monotonic()
        message = await ctx.send("Pinging...")
        await ctx.trigger_typing()
        ping = (time.monotonic() - before) * 1000
        ping = round(ping)
        await message.delete()
        await ctx.send(f"🏓 | My ping is **{ping}ms!**")

    @commands.command()
    async def remind(self, ctx, time: str) -> discord.Message:
        """Reminders."""
        pass


def setup(bot):
    bot.add_cog(General())
