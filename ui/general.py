import re
import time
import datetime 

import discord
from discord.ext import commands
from disputils import BotEmbedPaginator

from handlers.reminders import ReminderService
from handlers.leaderboard import Leaderboard

class General(commands.Cog, name="General"):
    """This cog contains some general commands to assist in the usage of Flux."""

    def __init__(self):
        pass

    def parse_time(self, time: str) -> datetime.datetime:
        time = re.match(r"(?:(?P<weeks>\d+)w)?(?:\s+)?(?:(?P<days>\d+)d)?(?:\s+)?(?:(?P<hours>\d+)h)?(?:\s+)?(?:(?P<minutes>\d+)m)?(?:\s+)?(?:(?P<seconds>\d+)s)?", time)
        time = time.groupdict()
        for k, v in time.items():
            if time[k] is None:
                time[k] = 0
        for k, v in time.items():
            time[k] = int(v)
        time = datetime.timedelta(weeks=time.get("weeks"), days=time.get("days"), hours=time.get("hours"), minutes=time.get("minutes"), seconds=time.get("seconds"))
        time = datetime.datetime.now() - time
        return time

    @commands.command()
    async def help(self, ctx) -> discord.Message:
        """Helps the user with Flux commands"""

        embeds = []
        blacklisted_cogs = ["Developer"]

        e = discord.Embed(color=ctx.author.color)
        e.set_author(name="Help", icon_url=ctx.bot.user.avatar_url)
        e.description = "Welcome to the interactive help menu!\nHere you can see the commands and their uses.\n\nTo use the interactive help menu use the reactions:\n:track_previous: To go to this menu.\n:arrow_backward: To go to the last page.\n:arrow_forward: To go to the next page.\n:track_next: To go to the last page.\n:stop_button: To stop the interactive help menu."
        embeds.append(e)

        for cog in ctx.bot.cogs:
            cog = ctx.bot.cogs[cog]
            if not cog.qualified_name in blacklisted_cogs:
                if cog.get_commands:
                    embed = discord.Embed(color=ctx.author.color)
                    embed.set_author(name=cog.qualified_name, icon_url=ctx.bot.user.avatar_url)
                    commands = list(cog.walk_commands())
                    embed.add_field(name="Commands:", value=":stop_button: To stop at any time.")
                    for command in commands:
                        if isinstance(command, discord.ext.commands.Group):
                            continue
                        if command.parent:
                            params = command.clean_params
                            params = "<" + ">, <".join(params) + ">"
                            embed.add_field(name=f"**{ctx.prefix}{command.parent} {command.name}** {params}", value=command.help, inline=False)
                        else:
                            params = command.clean_params
                            params = "<" + ">, <".join(params) + ">"
                            if params == "<>":
                                params = ""
                            embed.add_field(name=f"**{ctx.prefix}{command.name}** {params}", value=command.help, inline=False)
                    embeds.append(embed)
        p = BotEmbedPaginator(ctx, embeds)
        return await p.run()

    @commands.command()
    async def ping(self, ctx) -> discord.Message:
        """Ping pong!"""
        before = time.monotonic()
        message = await ctx.send("Pinging...")
        await ctx.trigger_typing()
        ping = (time.monotonic() - before) * 1000
        ping = round(ping)
        await message.delete()
        await ctx.send(f"🏓 | My ping is **{ping}ms!**")

    @commands.command()
    async def remind(self, ctx, to_remind: str, *time) -> discord.Message:
        """A reminder command. You can have more than one word by putting your reminder message in quotations. Example: "reminder words" """
        if not ctx.bot.db_client:
            return await ctx.send("Without the database running, this command is defunct. Please contact the bot maintainer.")
        time = " ".join(time)
        time = self.parse_time(time)
        await ReminderService(ctx.bot).new_reminder(ctx.author.id, to_remind, time)
        return await ctx.send("Reminder set!")

    @commands.command()
    async def leaderboard(self, ctx):
        """This shows a leaderboard of all the points."""
        if not ctx.bot.db_client:
            return await ctx.send("Without the database running, this command is defunct. Please contact the bot maintainer.")
        leaderboardhandler = Leaderboard()
        points = ctx.bot.db("guilds").find(str(ctx.guild.id)).get("points")
        if points is None:
            ctx.bot.db("guilds").update(str(ctx.guild.id), {"points": {}})
            return await ctx.send("No one has any points.  o.o")
        users = {}
        for k, v in points.items():
            users[k] = {"points": v}
        if users == {}:
            return await ctx.send("No one has any points.  o.o")

        await leaderboardhandler.create(ctx, users, sort_by="points")


def setup(bot):
    bot.add_cog(General())
