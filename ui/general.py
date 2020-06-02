import time
import random
import typing

import discord
from discord.ext import commands
from discord.ext.commands.core import GroupMixin

import handlers.paginator as paginator
from handlers.reminders import ReminderService
from handlers.leaderboard import Leaderboard
from handlers.helpformatter import HelpFormatter


class General(commands.Cog, name="General"):
    """This cog contains general commands to assist in the usage of Flux."""

    def __init__(self):
        pass

    def get_all_subcommands(self, command):
        yield command
        if type(command) is discord.ext.commands.core.Group:
            for subcmd in command.commands:
                yield from self.get_all_subcommands(subcmd)

    def get_all_commands(self, bot):
        """Returns a list of all command names for the bot"""
        # First lets create a set of all the parent names
        for cmd in bot.commands:
            yield from self.get_all_subcommands(cmd)

    @commands.command(name="help")
    async def _help(self, ctx, *, command=None):
        """This command right here!"""
        groups = {}
        entries = []
        blacklisted_cogs = ["Developer", "Insights"]
        cprefx = ctx.prefix.replace("!", "")
        cprefx = cprefx.replace(ctx.bot.user.mention, "@" + ctx.bot.user.name)

        if command is not None:
            command = ctx.bot.get_command(command)

        if command is None:
            for cmd in self.get_all_commands(ctx.bot):
                try:
                    can_run = await cmd.can_run(ctx)
                    if not can_run or not cmd.enabled or cmd.hidden:
                        continue
                    elif cmd.cog_name in blacklisted_cogs:
                        continue
                except commands.errors.MissingPermissions:
                    continue
                except commands.errors.CheckFailure:
                    continue

                cog = cmd.cog_name
                if cog in groups:
                    groups[cog].append(cmd)
                else:
                    groups[cog] = [cmd]

            for cog, cmds in groups.items():
                entry = {"title": "{} Commands".format(cog), "fields": []}

                for cmd in cmds:
                    if not cmd.help:
                        # Assume if there's no description for a command,
                        # it's not supposed to be used
                        # I.e. the !command command. It's just a parent
                        continue

                    alias = "(or "
                    aliases = cmd.aliases
                    count = len(aliases)
                    i = 0
                    for a in aliases:
                        i += 1
                        if count == i:
                            alias = alias + f"{a})"
                        else:
                            alias = alias + f"{a}, "
                    description = cmd.help.partition("\n")[0]
                    aliases = alias if len(cmd.aliases) > 0 else ""
                    name_fmt = f"{cprefx}**{cmd.qualified_name}** {aliases}"
                    entry["fields"].append(
                        {"name": name_fmt, "value": description, "inline": False}
                    )
                entries.append(entry)

            entries = sorted(entries, key=lambda x: x["title"])
            try:
                pages = paginator.DetailedPages(
                    ctx.bot, message=ctx.message, entries=entries
                )
                pages.embed.set_thumbnail(url=ctx.bot.user.avatar_url)
                await pages.paginate()
            except paginator.CannotPaginate as e:
                await ctx.send(str(e))
        else:
            Formatter = HelpFormatter()
            randchoice = random.choice
            colour = "".join([randchoice("0123456789ABCDEF") for x in range(6)])
            colour = int(colour, 16)

            pages = await Formatter.format_help_for(ctx, command)
            cmd = cprefx + command.qualified_name + " " + command.signature
            if isinstance(command, GroupMixin):
                if ctx.guild:
                    e = discord.Embed(colour=ctx.author.colour)
                    e.add_field(name=cmd, value=command.help, inline=False)
                    text = ""
                    all_subcommands = []  # idk how to do this
                    for name in command.all_commands:
                        all_subcommands.append(name)
                    for name in all_subcommands:
                        subcmd = command.all_commands[name]
                        if name in subcmd.aliases:
                            continue
                        text += f"**{subcmd.name}**: {subcmd.short_doc}\n"
                    e.add_field(name="Commands:", value=text, inline=False)
                    msg = f"Type {cprefx}help {command.qualified_name} command"
                    msg += " for more info on said command."
                    e.set_footer(text=msg)
                    return await ctx.send(embed=e)
            else:
                for page in pages:
                    if ctx.guild:
                        e = discord.Embed(color=ctx.author.colour)
                        e.add_field(name=cmd, value=page)
                    else:
                        e = discord.embed(color=colour)
                        e.add_field(name=cmd, value=page)
                return await ctx.send(embed=e)

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
            await ctx.send(
                "Without the database running, this command"
                " is defunct. "
                "Please use `.contact` with error:"
                " `ERR_CONN_FAILURE`"
            )
            return
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
                "You have no points."
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
                "Please use `.contact` with error:"
                " `ERR_CONN_FAILURE`"
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

    @commands.group(invoke_without_subcommand=True)
    async def prefix(self, ctx, *, prefix: typing.Optional[str] = None) -> None:
        """This command gets the prefix."""
        if not ctx.bot.db_client:
            await ctx.send(
                "Without the database running, this command"
                " is defunct. "
                "Please use `.contact` with error:"
                " `ERR_CONN_FAILURE`"
            )
            return
        if ctx.invoked_subcommand:
            return
        if prefix:
            await ctx.invoke(self._set, prefix=prefix)
            print("manual invoke")
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
        if not ctx.bot.db_client:
            await ctx.send(
                "Without the database running, this command"
                " is defunct. "
                "Please use `.contact` with error:"
                " `ERR_CONN_FAILURE`"
            )
            return
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
