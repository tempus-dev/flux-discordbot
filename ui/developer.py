import time

import discord
from discord.ext import commands


class Developer(commands.Cog, name="Developer"):
    """This cog contains all commands related to the development and maintence of Flux."""

    @commands.command()
    async def ping(self, ctx) -> discord.Message:
        before = time.monotonic()
        message = await ctx.send("Pinging...")
        await ctx.trigger_typing()
        ping = (time.monotonic() - before) * 1000
        ping = round(ping)
        await message.delete()
        await ctx.send(f"🏓 | My ping is **{ping}ms!**")


def setup(bot):
    bot.add_cog(Developer())
