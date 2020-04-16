from discord.ext import commands


class Tests(commands.Cog):
    pass  # I generally put random commands I'm testing here as part of development.


def setup(bot):
    bot.add_cog(Tests())
