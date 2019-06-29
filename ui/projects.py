import time

from typing import Union

import discord

from discord.ext import commands

from handlers.projects import ProjectHandler


class Projects(commands.Cog, name="Projects"):
    """This creates and handles projects."""

    def __init__(self, bot):
        self.bot = bot


    @commands.group(hidden=True)
    async def projects(self, ctx) -> None:
        """Project related commands."""
        ctx.projects = ProjectHandler(ctx.guild.id)

    @commands.has_permissions(manage_channels=True)
    @projects.command()
    async def create(self, ctx, name: str, owner: discord.Member=None) -> discord.Message:
        """This creates a project.
        You can set the owner to be someone other than you by providing a member."""

        owner = owner if owner is not None else ctx.author
        if ctx.bot.db("guilds").find(str(ctx.guild.id)) is None:
            ctx.bot.db("guilds").insert(str(ctx.guild.id), ctx.bot.empty_guild)

        # await ctx.send("Creating project channel...")
        if ctx.bot.db("guilds").find(str(ctx.guild.id)).get("category_channel") is None:
            overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                          ctx.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                          }
            category = await ctx.guild.create_category("Flux Projects", overwrites=overwrites)
            ctx.bot.db("guilds").update(str(ctx.guild.id), {"project_category": str(category.id)})

        overwrites = {owner: discord.PermissionOverwrite(read_messages=True, send_messages=False, add_reactions=True),
            ctx.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)}

        channel = await ctx.guild.create_text_channel(f"{name}-project", category=category, overwrites=overwrites)
        await channel.send(f"Project Owner: {ctx.author}")
        message = await channel.send("Project Progress: |----------------------| 0.0% Complete")
        await message.pin()
        ctx.projects.create_project(owner.id, owner.id, name, channel.id, message.id)
        await ctx.send("Project created!")

    @projects.command()
    async def status(self, ctx, project_name: str) -> discord.Message:
        """This returns the status of a project."""
        progress_bar = ctx.projects.project_progress_bar(project_name)
        if progress_bar is None:
            progress_bar = "Project Progress: |----------------------| 0.0% Complete"
        await ctx.send(progress_bar)

    @projects.command()
    async def add(self, ctx, project: str, members: commands.Greedy[discord.Member]) -> discord.Message:
        """This adds as many project members as you want to your project.
        This command is limited to the project owner only."""
        if str(ctx.author.id) != ctx.projects.find_project(project).get("owner"):
            return await ctx.send("You can't add members to this project.  o.o")
        members = members if len(members) > 0 else [ctx.author]
        count = len(members)
        channel = ctx.guild.get_channel(int(ctx.projects.find_project(project).get("channel")))
        for member in members:
            await channel.set_permissions(member, read_messages=True, send_messages=False)
        ctx.projects.add_project_members(project, [x.id for x in members])
        if members == ctx.author:
            return await ctx.send(f"You're already a member.  o.o")
        if count == 1:
            member = members[0]
            return await ctx.send(f"`{member}` is now a member.")
        if count == 2:
            return await ctx.send(f"`{members[0]}` and `{members[1]}` are now members.")
        else:
            last_member = members[count - 1]
            members = members.pop(count - 1)
            string = "`"
            members = string + ", ".join(str(x) for x in members) + string
            members = members + f" and `{last_member}`"
            return await ctx.send(f"{members} are now members of your project.")

    @commands.Cog.listener()
    async def on_project_member_add(self, guild_id: int, project: dict, members: list) -> discord.Message:
        """This fires when members are added."""
        # print(project)
        guild = (await self.bot.fetch_guild(guild_id))
        channel = await self.bot.fetch_channel(int(project.get("channel")))
        members = [(await guild.fetch_member(member)) for member in members]
        count = len(members)
        if count == 1:
            member = members[0]
            return await channel.send(f"**> Member Update:** `{member}` was added to this project.")
        if count == 2:
            return await channel.send(f"**> Member Update:** `{members[0]}` and `{members[1]}` were added to this project.")
        else:
            last_member = members[count - 1]
            members = members.pop(count - 1)
            string = "`"
            members = string + "`, ".join(str(x) for x in members) + string
            members = members + f" and `{last_member}`"
            return await channel.send(f"**> Member Update:** {members} were added to this project.")
        
def setup(bot):
    bot.add_cog(Projects(bot))