import os
import io
import sys
import time
import asyncio
import inspect
import textwrap
import traceback
from contextlib import redirect_stdout
from handlers.pathing import path

import git
import discord
from discord.ext import commands


class Developer(commands.Cog, name="Developer"):
    """This cog contains all commands related to the development and maintence of Flux."""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    async def cog_check(self, ctx):
        return ctx.author.id in ctx.bot.config.owners

    def pagify(self, text, delims=["\n"], *, escape=True, shorten_by=8,
               page_len=1000):
        """DOES NOT RESPECT MARKDOWN BOXES OR INLINE CODE"""
        in_text = text
        if escape:
            num_mentions = text.count("@here") + text.count("@everyone")
            shorten_by += num_mentions
        page_len -= shorten_by
        while len(in_text) > page_len:
            closest_delim = max([in_text.rfind(d, 0, page_len)
                                 for d in delims])
            closest_delim = closest_delim if closest_delim != -1 else page_len
            if escape:
                to_send = self.escape_mass_mentions(in_text[:closest_delim])
            else:
                to_send = in_text[:closest_delim]
            yield to_send
            in_text = in_text[closest_delim:]

        if escape:
            yield self.escape_mass_mentions(in_text)
        else:
            yield in_text

    def box(self, text, lang=""):
        ret = f"```{lang}\n{text}\n```"
        return ret

    def escape(self, text, *, mass_mentions=False, formatting=False):
        if mass_mentions:
            text = text.replace("@everyone", "@\u200beveryone")
            text = text.replace("@here", "@\u200bhere")
        if formatting:
            text = (text.replace("`", "\\`")
                        .replace("*", "\\*")
                        .replace("_", "\\_")
                        .replace("~", "\\~"))
        return text

    def escape_mass_mentions(self, text):
        return self.escape(text, mass_mentions=True)

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f"""```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}:
        {e}```"""

    @commands.command()
    async def git(self, ctx, *pull) -> None:
        """Pull code from github."""
        g = git.cmd.Git("./")
        e = discord.Embed(color=ctx.author.color)
        e.set_author(name="Git Pull", icon_url=ctx.bot.user.avatar_url)
        e.add_field(name="Status:", value=g.pull())
        await ctx.send(embed=e)

    @commands.command(name='eval')
    async def _eval(self, ctx, *, body: str) -> discord.Message:
        """Evaluates code"""
        pagify = self.pagify
        box = self.box

        env = {
            'bot': ctx.bot,
            'flux': ctx.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            'discord': discord,
            'os': os,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            for page in pagify(text=f"{e.__class__.__name__}: {e}"):
                return await ctx.send(box(page, lang="py"))

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            for page in pagify(text=f"{value}{traceback.format_exc()}"):
                return await ctx.send(box(page, lang="py"))
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except Exception as e:
                pass

            if ret is None:
                if value:
                    for page in pagify(text=f"{value}"):
                        return await ctx.send(box(page, lang="py"))
            else:
                self._last_result = ret
                for page in pagify(text=f"{value}{ret}"):
                    return await ctx.send(box(page, lang="py"))

    @commands.command()
    async def ping(self, ctx) -> discord.Message:
        before = time.monotonic()
        message = await ctx.send("Pinging...")
        await ctx.trigger_typing()
        ping = (time.monotonic() - before) * 1000
        ping = round(ping)
        await message.delete()
        await ctx.send(f"🏓 | My ping is **{ping}ms!**")

    @commands.command(name='r')
    async def reload(self, ctx):
        """Reloading all the cogs"""
        broken_cogs = []
        extensions = []
        folders = ['ui']
        for folder in folders:
            extensions.extend([f'{folder}.{x[:-3]}' for x in os.listdir(path(folder)) if all(((x[-3:] == '.py'), (x != '__init__.py')))])
        for i in extensions:
            try:
                self.bot.unload_extension(i)
                self.bot.load_extension(i)
            except commands.ExtensionNotLoaded:
                self.bot.load_extension(i)
            except Exception as e:
                broken_cogs.append(f'{i}: [{type(e).__name__} - {e}]\n')
                continue
        if len(broken_cogs) >= 1:
            broken_cogs = '\n'.join(str(y) for y in broken_cogs)
            await ctx.send(f'**Broken cogs(s):**\n```css\n{broken_cogs}```', delete_after=30)
        else:
            await ctx.send(f'**{len(extensions)}** cog(s) successfully reloaded', delete_after=10)

    @commands.command()
    async def exit(self, ctx):
        """Logs out the bot"""
        print('Logging out')
        await ctx.bot.logout()

    @commands.command()
    async def embeding(self, ctx):
        embed = discord.Embed(name='Test embed', value='another test', colour=0xc27c0e, timestamp=now())
        embed.add_field(name=f'Greetings, human! (assuming)', value='Like, prepare to do things and stuff man', inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Developer(bot))
