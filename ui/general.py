import re
import time
import datetime

import discord
from discord.ext import commands
from disputils import BotEmbedPaginator

from handlers.reminders import ReminderService
from handlers.leaderboard import Leaderboard


class General(commands.Cog, name="General"):
    """This cog contains general commands to assist in the usage of Flux."""

    def __init__(self):
        pass

    def parse_time(self, time_re: str) -> datetime.datetime:
        time_re = re.match(
            r"(?:(?P<weeks>\d+)w)?(?:\s+)?(?:(?P<days>\d+)d)?(?:\s+)?(?:(?P<hours>\d+)h)?(?:\s+)?(?:(?P<minutes>\d+)m)?(?:\s+)?(?:(?P<seconds>\d+)s)?", time_re)
        time_re = time_re.groupdict()
        for k, v in time_re.items():
            if not time_re[k]:
                time_re[k] = 0
        for k, v in time_re.items():
            time_re[k] = int(v)

        time_re = datetime.timedelta(
            weeks=time_re.get("weeks"),
            days=time_re.get("days"),
            hours=time_re.get("hours"),
            minutes=time_re.get("minutes"),
            seconds=time_re.get("seconds")
        )
        time_re = datetime.datetime.now() - time_re
        return time_re

    @commands.command()
    async def help(self, ctx) -> discord.Message:
        """Helps the user with Flux commands"""

        embeds = []
        blacklisted_cogs = ["Developer", "Insights"]
        prefix = ctx.prefix

        e = discord.Embed(color=ctx.author.color)
        e.set_author(name="Help", icon_url=ctx.bot.user.avatar_url)
        description = """Welcome to the interactive help menu!
Here you can see the commands and their uses.

To use the interactive help menu use the reactions:
:track_previous: To go to this menu.
:arrow_backward: To go to the last page.
:arrow_forward: To go to the next page.
:track_next: To go to the last page.
:stop_button: To stop the interactive help menu.
        """
        e.description = description
        embeds.append(e)

        for cog in ctx.bot.cogs:
            cog = ctx.bot.cogs[cog]
            if cog.qualified_name not in blacklisted_cogs:
                if cog.get_commands:
                    embed = discord.Embed(color=ctx.author.color)
                    embed.set_author(name=cog.qualified_name,
                                     icon_url=ctx.bot.user.avatar_url)
                    commands = list(cog.walk_commands())
                    embed.add_field(name="Commands:",
                                    value=":stop_button: To stop at any time.")
                    for command in commands:
                        if isinstance(command, discord.ext.commands.Group):
                            continue
                        if command.parent:
                            params = command.clean_params
                            params = "<" + ">, <".join(params) + ">"
                            embed.add_field(
                                name=f"**{ctx.prefix}{command.parent}"
                                f" {command.name}** {params}",
                                value=command.help, inline=False)
                        else:
                            params = command.clean_params
                            params = "<" + ">, <".join(params) + ">"
                            if params == "<>":
                                params = ""
                            embed.add_field(
                                name=f"**{prefix}{command.name}** {params}",
                                value=command.help, inline=False)

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
    async def remind(self, ctx, to_remind: str, *duration) -> discord.Message:
        """A reminder command.

        You can put 2+ words by putting your reminder message in quotes.
        Example: "reminder words" """
        if not ctx.bot.db_client:
            return await ctx.send("Without the database running, this command"
                                  " is defunct. "
                                  "Please contact the bot maintainer.")
        if not duration:
            raise commands.MissingRequiredArgument(
                ctx.commmand.clean_params['duration']
            )
        duration = " ".join(duration)
        duration = self.parse_time(duration)
        await ReminderService(ctx.bot).new_reminder(
            ctx.author.id, to_remind, duration)
        return await ctx.send("Reminder set!")

    @commands.command(name='points')
    async def points(self, ctx, user: discord.Member = None) -> None:
        """Check yours or someone else's points."""
        if not ctx.bot.db_client:
            await ctx.send("Without the database running, this command"
                           " is defunct. "
                           "Please use `.contact` with error:"
                           " `ERR_CONN_FAILURE`"
                           )
            return

        if not user:
            user = ctx.author
        if not ctx.bot.db("guilds").find(str(ctx.guild.id)):
            await ctx.send("No one has any points.")
            return

        points = ctx.bot.db("guilds").find(str(ctx.guild.id)).get("points")

        if not points:
            await ctx.send("No one has any points.")
            return

        if not points.get(str(user.id)):
            await ctx.send(f"You have no points.") if \
                ctx.author == user else \
                await ctx.send(f"`{user}` has no points.")
            return

        points = f"{points} points" if points != 1 else f"{points} point"

        await ctx.send(f"`{user}` has `{points}`.") if not \
            user == ctx.author else \
            await ctx.send(f"You have `{points}`.")
        return

    @commands.command()
    async def leaderboard(self, ctx):
        """This shows a leaderboard of all the points."""
        if not ctx.bot.db_client:
            await ctx.send("Without the database running, this command"
                           " is defunct. "
                           "Please contact the bot maintainer."
                           )
            return
        leaderboardhandler = Leaderboard()
        if not ctx.bot.db("guilds").find(str(ctx.guild.id)):
            await ctx.send("No one has any points.")
            return
        points = ctx.bot.db("guilds").find(str(ctx.guild.id)).get("points")
        if not points:
            ctx.bot.db("guilds").update(str(ctx.guild.id), {"points": {}})
            await ctx.send("No one has any points.")
            return
        users = {}
        for k, v in points.items():
            users[k] = {"points": v}
        if users == {}:
            return await ctx.send("No one has any points.  o.o")

        await leaderboardhandler.create(ctx, users, sort_by="points")


def setup(bot):
    bot.add_cog(General())
