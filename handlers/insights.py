import string
import discord

from discord.ext import commands
from typing import Optional
from datetime import datetime as dt
from random import SystemRandom as sysrand


class Insights(commands.Cog):
    """This tracks overall bot usage."""

    def __init__(self, bot):
        self.bot = bot

    def increment_cmd(self, cmd) -> None:
        db = self.bot.db("logs")
        if not db.find(cmd):
            db.insert(cmd, {"usage": 1})
            return
        usage = db.find(cmd)["usage"]
        db.update(cmd, {"usage": usage + 1})

    async def log_error(self, error) -> str:
        db = self.bot.db("logs")
        if not db.find("errors"):
            db.insert("errors", {})
        lower = string.ascii_lowercase
        digits = string.digits
        uuid = "".join(sysrand().choice(lower + digits) for _ in range(8))
        err = {
            uuid: {
                "cmd": None,
                "error": error,
                "author": None,
                "channel": None,
                "guild": None,
                "time": None,
            }
        }
        db.update("errors", err)
        embed = discord.Embed()
        embed.title = f"Non command exception occurred"
        embed.description = f"```py\n{error}\n```"
        embed.timestamp = dt.now()  # TODO: confirm that I can pass dt.now()
        embed.set_author(name=f"Error ID: {uuid}")

        channel = await self.get_err_logs()
        try:
            await channel.send(embed=embed)
        except discord.errors.HTTPException:
            desc = embed.description
            first = desc[:2044] + "\n```"
            second = "```py\n" + desc[2044:]
            embed.description = first
            await channel.send(embed=embed)
            embed = discord.Embed(title="Exception continued", description=second)
            await channel.send(embed=embed)

        return uuid

    async def log_cmd_error(self, ctx, error) -> str:
        cmd = ctx.command.qualified_name
        db = self.bot.db("logs")
        if not db.find("errors"):
            db.insert("errors", {})
        lower = string.ascii_lowercase
        digits = string.digits
        uuid = "".join(sysrand().choice(lower + digits) for _ in range(8))
        err = {
            uuid: {
                "cmd": cmd,
                "error": error,
                "author": str(ctx.author.id),
                "channel": str(ctx.channel.id),
                "guild": str(ctx.guild.id),
                "time": str(ctx.message.created_at),
            }
        }
        db.update("errors", err)
        cid = ctx.channel.id
        aid = ctx.author.id
        embed = discord.Embed()
        embed.title = f"Exception in command {cmd}"
        embed.description = f"```py\n{error}\n```"
        embed.timestamp = ctx.message.created_at
        embed.set_footer(text=f"Author: {aid} • Channel: {cid}")
        embed.set_author(name=f"Error ID: {uuid}")

        channel = await self.get_err_logs()
        try:
            await channel.send(embed=embed)
        except discord.errors.HTTPException:
            desc = embed.description
            first = desc[:2044] + "\n```"
            second = "```py\n" + desc[2044:]
            embed.description = first
            await channel.send(embed=embed)
            embed = discord.Embed(title="Exception continued", description=second)
            await channel.send(embed=embed)

        return uuid

    async def get_server_logs(self) -> Optional[discord.TextChannel]:
        server_logs = self.bot.config.server_logs
        try:
            chan = await self.bot.fetch_channel(server_logs)
        except discord.errors.NotFound:
            return
        return chan

    async def get_cmd_logs(self) -> Optional[discord.TextChannel]:
        cmd_logs = self.bot.config.command_logs
        try:
            chan = await self.bot.fetch_channel(cmd_logs)
        except discord.errors.NotFound:
            return
        return chan

    async def get_err_logs(self) -> Optional[discord.TextChannel]:
        err_logs = self.bot.config.error_logs
        try:
            chan = await self.bot.fetch_channel(err_logs)
        except discord.errors.NotFound:
            return
        return chan

    @commands.command()
    async def error(self, ctx, uuid: str) -> None:
        db = self.bot.db("logs")
        if not db.find("errors"):
            await ctx.send("Doesn't exist.")
        elif not db.find("errors").get(uuid):
            await ctx.send("Doesn't exist.")
        else:
            error = db.find("errors").get(uuid)
            cmd = error.get("cmd")
            embed = discord.Embed()
            embed.title = f"Exception in command {cmd}"
            embed.description = f"```py\n{error.get('error')}\n```"
            embed.timestamp = dt.strptime(error.get("time"), "%Y-%m-%d %H:%M:%S.%f")
            errchn = error.get("channel")
            errusr = error.get("author")
            embed.set_footer(text=f"Author: {errusr} • Channel: {errchn}")
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild) -> None:
        embed = discord.Embed(title=f"Added to guild {guild.name}.")
        embed.set_footer(
            text=f"Member count: {len(guild.members)} • Guild ID: {guild.id}"
            f" • {self.bot.user.name} is in {len(self.bot.guilds)}"
        )
        channel = await self.get_server_logs()
        msg = await channel.send("-")
        await msg.delete()
        embed.timestamp = msg.created_at
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild) -> None:
        embed = discord.Embed(title=f"Removed from guild {guild.name}.")
        embed.set_footer(
            text=f"Member count: {len(guild.members)} • Guild ID: {guild.id}"
            f" • {self.bot.user.name} is in {len(self.bot.guilds)}"
        )
        channel = await self.get_server_logs()
        msg = await channel.send("-")
        await msg.delete()
        embed.timestamp = msg.created_at
        await channel.send(embed=embed)
        # TODO: Last command run.
        channel = await self.get_server_logs()
        await channel.send(msg)

    @commands.Cog.listener()
    async def on_command(self, ctx) -> None:
        embed = discord.Embed(
            title=f"Command `{ctx.command.qualified_name}` was executed.",
            timestamp=ctx.message.created_at,
        )
        embed.timestamp = ctx.message.created_at
        embed.add_field(name="Author", value=ctx.author, inline=True)
        if ctx.guild:
            embed.add_field(name="Guild", value=ctx.guild.name, inline=True)
            embed.add_field(name="Channel", value=ctx.channel.name, inline=True)
            embed.set_footer(
                text=f"{ctx.author.id} • {ctx.guild.id} • {ctx.channel.id}"
            )
        else:
            embed.add_field(name="Channel", value="DMs", inline=True)
            embed.set_footer(text=f"{ctx.author.id}")
        self.increment_cmd(ctx.command.qualified_name)
        channel = await self.get_cmd_logs()
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Insights(bot))
