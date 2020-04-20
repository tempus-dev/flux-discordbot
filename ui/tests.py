from discord.ext import commands


class Tests(commands.Cog):
    # I generally put random commands I'm testing here as part of development.

    @commands.command()
    async def test(self, ctx):
        raise NotImplementedError


def setup(bot):
    bot.add_cog(Tests())
