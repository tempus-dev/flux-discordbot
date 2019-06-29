import datetime
from disputils import BotEmbedPaginator
import discord

class Leaderboard:
    """Creates leaderboard embeds from user data for disputils paginator"""

    async def create(self, ctx, users: dict, sort_by: str):
        msg = await ctx.send("Loading...")
        to_sort = self.extract(users, sort_by)
        sorted_users = sorted(to_sort, key=to_sort.get, reverse=True)

        embeds = await self.create_embeds(
            ctx=ctx,
            sorted_users = sorted_users,
            to_sort = to_sort,
            title = "Leaderboard",
            icon_url = ctx.guild.icon_url,
            color = ctx.author.color)

        paginator = BotEmbedPaginator(ctx, embeds)
        await msg.delete()
        await paginator.run()

    def extract(self, users: dict, extract_by: str):
        extracted = {}
        for user in users:
            extracted[user] = users[user][extract_by]
        return extracted

    async def create_embeds(self, ctx, sorted_users, to_sort, title, icon_url, color):
        embeds = []
        start = 0
        end = 10
        n = 1
            
        for i in range(round(len(sorted_users)/10)+1):
            embed = discord.Embed(color=color)
            embed.set_author(name=title, icon_url=icon_url)
            for user in sorted_users[start:end]:
                name = str(n) + ". " + str(await ctx.bot.fetch_user(int(user))) 
                embed.add_field(name=name, value=to_sort[user])
                n += 1
            embeds.append(embed)
            start += 10
            end += 10
        return embeds



