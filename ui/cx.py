import discord
from discord.ext import commands


class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def contact(self, ctx, *message) -> discord.Message:
        """Contacts the developers for any issues."""
        cfg = self.bot.config
        try:
            cid = cfg.contact_channel_id
            contact_channel = cfg.contact_channel
            if not contact_channel:
                contact_channel = await self.bot.fetch_channel(cid)
        except discord.errors.NotFound:
            contact_channel = await self.bot.fetch_user(cfg.owners[0])

        message = " ".join(message)
        if len(message) > 1000:
            return await ctx.send("Your request is a fairly long! "
                                  "Please shorten it, and if that isn't "
                                  "possible you can contact saying you "
                                  "need to explain it out, and a developer "
                                  "will get back to you.")
        embed = discord.Embed(colour=ctx.author.colour,
                              title=f"{ctx.author}"
                              " has filed a request.")
        embed.add_field(name="Message:", value=f"```\n{message}\n```")
        embed.set_footer(text=f"User ID: {ctx.author.id}"
                         f" Guild: {ctx.guild.name}"
                         f"({ctx.guild.id})")
        await contact_channel.send(embed=embed)
        await ctx.send("The message has been sent successfully! "
                       "Make sure your DMs are open to receive the response, "
                       "and the developers will get back to "
                       "you when they can")


def setup(bot):
    bot.add_cog(Support(bot))
