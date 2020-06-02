import time

import discord
from discord.ext import commands
from disputils import BotEmbedPaginator

from handlers.reminders import ReminderService
from handlers.leaderboard import Leaderboard


class General(commands.Cog, name="General"):
    """This cog contains general commands to assist in the usage of Flux."""

    def __init__(self):
        pass

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
            if cog.qualified_name in blacklisted_cogs or not cog.get_commands:
                continue
            embed = discord.Embed(color=ctx.author.color)
            embed.set_author(name=cog.qualified_name, icon_url=ctx.bot.user.avatar_url)
            commands = list(cog.walk_commands())
            embed.add_field(
                name="Commands:", value=":stop_button: To stop at any time."
            )
            for command in commands:
                if isinstance(command, discord.ext.commands.Group):
                    continue
                if command.parent:
                    params = command.clean_params
                    params = "<" + ">, <".join(params) + ">"
                    embed.add_field(
                        name=f"**{ctx.prefix}{command.parent}"
                        f" {command.name}** {params}",
                        value=command.help,
                        inline=False,
                    )
                else:
                    params = command.clean_params
                    params = "<" + ">, <".join(params) + ">"
                    if params == "<>":
                        params = ""
                    embed.add_field(
                        name=f"**{prefix}{command.name}** {params}",
                        value=command.help,
                        inline=False,
                    )

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
            return await ctx.send(
                "Without the database running, this command"
                " is defunct. "
                "Please contact the bot maintainer."
            )
        if not duration:
            raise commands.MissingRequiredArgument(
                ctx.commmand.clean_params["duration"]
            )
        duration = " ".join(duration)
        duration = ctx.bot.parse_time(duration)
        await ReminderService(ctx.bot).new_reminder(ctx.author.id, to_remind, duration)
        return await ctx.send("Reminder set!")

    @commands.command(name="points")
    async def points(self, ctx, user: discord.Member = None) -> None:
        """Check yours or someone else's points."""
        if not ctx.bot.db_client:
            await ctx.send(
                "Without the database running, this command"
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
            await ctx.send(
                f"You have no points."
            ) if ctx.author == user else await ctx.send(f"`{user}` has no points.")
            return

        points = f"{points} points" if points != 1 else f"{points} point"

        await ctx.send(
            f"`{user}` has `{points}`."
        ) if not user == ctx.author else await ctx.send(f"You have `{points}`.")
        return

    @commands.command()
    async def leaderboard(self, ctx):
        """This shows a leaderboard of all the points."""
        if not ctx.bot.db_client:
            await ctx.send(
                "Without the database running, this command"
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

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx, *, prefix: typing.Optional[str] = None) -> None:
        """This command gets the prefix."""
        if ctx.invoked_subcommand:
            return
        if not ctx.guild:
            text = f"{ctx.bot.user.name}'s prefix is"
            text = text + f" `{ctx.bot.config.prefix}`"
            embed = discord.Embed(description=text)
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(color=ctx.author.color)
        embed.set_footer(text="You can also mention the bot as a prefix anywhere.")
        if not ctx.bot.db("guilds").find(str(ctx.guild.id)):
            text = f"{ctx.bot.user.name}'s "
            text = text + f"prefix is `{ctx.bot.config.prefix}`"
            embed.description = text

            await ctx.send(embed=embed)
            return

        prefixes = ctx.bot.db("guilds").find(str(ctx.guild.id)).get("prefix")
        if not prefixes:
            prefixes = [ctx.bot.config.prefix]
        _len = len(prefixes)
        name = (
            f"{ctx.guild.name}'s"
            if ctx.guild.name[-1:] != "s"
            else f"{ctx.guild.name}'"
        )
        if _len == 1:
            text = f"{name} prefix for "
            text = text + f"{ctx.bot.user.name} is `{prefixes[0]}`"
        elif _len == 2:
            text = f"{name} prefixes for {ctx.bot.user.name} are"
            text = text + f" `{prefixes[0]}` and `{prefixes[1]}`"
        elif _len > 2:
            last = prefixes[_len - 1]
            prefixes = prefixes.pop((_len - 1))
            text = f"{name} prefixes for {ctx.bot.user.name} are "
            text = text + f"`{'`, '.join(x for x in prefixes)} and `{last}`"

        embed.description = text
        await ctx.send(embed=embed)

    @commands.has_permissions(manage_messages=True)
    @prefix.command(name="set")
    async def _set(self, ctx, *, prefix) -> None:
        """This sets a prefix.

        You must have manage messages to use this command."""
        if not ctx.guild:
            return
        guild_db = ctx.bot.db("guilds").find(str(ctx.guild.id))
        if not guild_db:
            ctx.bot.db("guilds").insert(str(ctx.guild.id), ctx.bot.empty_guild)
            guild_db = ctx.bot.db("guilds").find(str(ctx.guild.id))
        if not guild_db.get("prefix"):
            guild_db["prefix"] = []
            ctx.bot.db("guilds").update(str(ctx.guild.id), guild_db)

        guild_db["prefix"].extend(prefix.split(" "))
        ctx.bot.db("guilds").update(str(ctx.guild.id), guild_db)
        await ctx.send("Alright! Your prefix settings have been updated.")

    @commands.has_permissions(manage_messages=True)
    @prefix.command(name="del", aliases=["delete"])
    async def _del(self, ctx, *, prefix) -> None:
        """This deletes a prefix.

        You must have manage messages to use this command."""
        if not ctx.guild:
            return
        guild_db = ctx.bot.db("guilds").find(str(ctx.guild.id))
        if not guild_db:
            ctx.bot.db("guilds").insert(str(ctx.guild.id), ctx.bot.empty_guild)
            guild_db = ctx.bot.db("guilds").find(str(ctx.guild.id))
        if not guild_db.get("prefix"):
            guild_db["prefix"] = [ctx.bot.config.prefix]
            ctx.bot.db("guilds").update(str(ctx.guild.id), guild_db)

        [guild_db["prefix"].remove(x) for x in prefix.split(" ")]
        ctx.bot.db("guilds").update(str(ctx.guild.id), guild_db)
        await ctx.send("Alright! Your prefix settings have been updated.")

    @commands.command()
    async def invite(self, ctx) -> None:
        """Gets the bot invite."""
        embed = discord.Embed()
        uid = ctx.bot.user.id
        inv = f"http://discord.com/api/oauth2/authorize?client_id={uid}"
        inv = inv + "&scope=bot&permissions=388176"
        desc = "Thanks for choosing Flux!"
        embed.description = desc + f" My invite is [here!]({inv})"
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(General())
