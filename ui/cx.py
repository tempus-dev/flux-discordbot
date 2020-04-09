import discord
from discord.ext import commands 

class cx(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 

    @commands.command()
    async def contact(self, ctx, *message) -> discord.Message:
        """Contacts the developers for any issues."""
        try:
            contact_channel = await self.bot.fetch_channel(self.bot.config.contact_channel_id)
        except discord.errors.NotFound:
            contact_channel = await self.bot.fetch_user(self.bot.config.owners[0])

        message = " ".join(message)
        if len(message) > 1000:
            return await ctx.send("Your request is a fairly long! Please shorten it, and if that isn't possible, "
                                  "you can contact saying you need to explain it out, and a developer will friend request you.")
        embed = discord.Embed(colour=ctx.author.colour, title=f"{ctx.author} has filed a request.")
        embed.add_field(name="Message:", value=f"```\n{message}\n```")
        embed.set_footer(text=f"User ID: {ctx.author.id} Guild: {ctx.guild.name} ({ctx.guild.id})")
        await contact_channel.send(embed=embed)
        await ctx.send("The message has been sent successfully! " 
                      "Make sure your DMs are open to receive the response, and the developers will get back to you when they can.")

def setup(bot):
    bot.add_cog(cx(bot))