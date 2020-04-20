import discord

from discord.ext import commands

from handlers.projects import ProjectHandler


class Projects(commands.Cog, name="Projects"):
    """This creates and handles projects."""

    def __init__(self, bot):
        self.bot = bot
        e = "Project Progress: |----------------------| 0.0% Complete"
        self.empty_progress_bar = e

    @commands.group(hidden=True)
    async def projects(self, ctx) -> None:
        """Project related commands."""
        ctx.projects = ProjectHandler(ctx.guild.id)

    @commands.has_permissions(manage_channels=True)
    @projects.command()
    async def create(self, ctx, name: str,
                     owner: discord.Member = None) -> discord.Message:
        """This creates a project.
        owner allows you to set an owner, default is you."""
        if ctx.projects.find_project(name):
            project = ctx.projects.find_project(name)
            if ctx.guild.get_Channel(int(project.get("channel"))):
                return await ctx.send("A project with that name exists.")
            else:
                await ctx.send("A project with this name exists but, a related"
                               " project channel was not found. "
                               "I will be overwriting the previous project.")
                ctx.projects.delete_project(name)

        owner = owner if owner is not None else ctx.author
        if ctx.bot.db("guilds").find(str(ctx.guild.id)) is None:
            ctx.bot.db("guilds").insert(str(ctx.guild.id), ctx.bot.empty_guild)

        # await ctx.send("Creating project channel...")
        if ctx.bot.db("guilds").find(
                str(ctx.guild.id)).get("project_category") is None:
            overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(
                read_messages=False),
                ctx.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True)
            }
            category = await ctx.guild.create_category("Flux Projects",
                                                       overwrites=overwrites)
            ctx.bot.db("guilds").update(str(ctx.guild.id), {
                "project_category": str(category.id)})

        else:
            category = ctx.guild.get_channel(
                int(ctx.bot.db("guilds").find(
                    str(ctx.guild.id)).get("project_category")))

        overwrites = {owner: discord.PermissionOverwrite(read_messages=True,
                                                         send_messages=False,
                                                         add_reactions=True),
                      ctx.me: discord.PermissionOverwrite(read_messages=True,
                                                          send_messages=True),
                      ctx.guild.default_role: discord.PermissionOverwrite(
                          read_messages=False)}

        channel = await ctx.guild.create_text_channel(f"{name}-project",
                                                      category=category,
                                                      overwrites=overwrites)
        await channel.send(f"Project Owner: {ctx.author}")
        message = await channel.send(self.empty_progress_bar)
        await message.pin()
        res = ctx.projects.create_project(
            owner.id, owner.id, name, channel.id, message.id)
        if res is None:
            return await ctx.send("An error has occurred. Use `.contact`"
                                  " with error: `PROJECT_STILL_EXISTS`")
        return await ctx.send("Project created!")

    @projects.command()
    async def delete(self, ctx, project_name: str) -> None:
        """This deletes a project."""
        if not ctx.projects.find_project(project_name):
            channel = discord.utils.get(
                ctx.guild.channels, name=f"{project_name}-project")

            if channel and channel.category.name == "Flux Projects":
                if ctx.author.permissions_in(channel).manage_channel:
                    message = await ctx.send("That project doesn't appear to"
                                             " exist in my database, but the "
                                             "channel still exists. "
                                             "Would you like to delete it?")
                    yes = "<:greenTick:596576670815879169>"
                    no = "<:redTick:596576672149667840>"
                    await message.add_reaction(yes)
                    await message.add_reaction(no)
                    reaction, user = await ctx.bot.wait_for(
                        "reaction_add",
                        check=lambda reaction, user: (user == ctx.author) and
                        (str(reaction.emoji) == yes or no) and
                        (reaction.message.channel == ctx.channel)
                    )
                    if reaction.emoji.id == ctx.bot.config.tick_yes:
                        channel_id = ctx.projects.find_project(
                            project_name).get("channel")
                        channel = await ctx.guild.fetch_channel(
                            channel_id
                        )
                        await channel.delete(reason="Project not found.")
                        await ctx.send("The channel was deleted sucessfully.")
                        return

                    elif reaction.emoji.id == ctx.bot.config.tick_no:
                        await ctx.send("Not deleting the channel.")
                        return

                else:  # If author doesn't have access to deleting channels.
                    await ctx.send("That project does not appear to be in my "
                                   "database, but the channel for it still "
                                   "exists. Please have someone with"
                                   " manage channels run this chommand."
                                   )
                    return
            else:
                await ctx.send("I could not find this project.")
                return

        if str(ctx.author.id) != ctx.projects.find_project(project_name).get(
                "owner"):
            await ctx.send("Only the owner can delete the project.")
            return
        message = await ctx.send("This action __cannot__ be undone. "
                                 "Once you do this, everything is gone. "
                                 "Are you sure you want to continue?")
        yes = "<:greenTick:596576670815879169>"
        no = "<:redTick:596576672149667840>"
        await message.add_reaction(yes)
        await message.add_reaction(no)
        reaction, user = await ctx.bot.wait_for(
            "reaction_add", check=lambda reaction, user:
            (user == ctx.author) and
            (str(reaction.emoji) == yes or no) and
            (reaction.message.channel == ctx.channel)
        )
        if reaction.emoji.id == ctx.bot.config.tick_yes:
            channel = ctx.projects.find_project(
                project_name).get("channel")
            channel = discord.utils.get(ctx.guild.channels,
                                        id=channel)
            ctx.projects.delete_project(project_name)
            if channel:
                await channel.delete(reason="Project deleted.")
            await ctx.send("The project has been deleted.")
        elif reaction.emoji.id == ctx.bot.config.tick_no:
            await ctx.send("Not deleting the project.")

    @projects.command()
    async def status(self, ctx, project_name: str) -> discord.Message:
        """This returns the status of a project."""
        progress_bar = ctx.projects.project_progress_bar(project_name)
        if progress_bar is None:
            progress_bar = self.empty_progress_bar
        await ctx.send(progress_bar)

    @projects.command()
    async def add(self, ctx, project_name: str,
                  members: commands.Greedy[discord.Member]) -> None:
        """This adds as many project members as you want to your project.
        This command is limited to the project owner only."""
        project = project_name
        if str(ctx.author.id) != ctx.projects.find_project(project).get(
                "owner"):
            await ctx.send("You can't add members to this project.")
        members = members if len(members) > 0 else [ctx.author]
        count = len(members)
        channel = ctx.guild.get_channel(
            int(ctx.projects.find_project(project).get("channel")))
        for member in members:
            await channel.set_permissions(member, read_messages=True,
                                          send_messages=False)
        ctx.projects.add_project_members(project, [x.id for x in members])
        if members == ctx.author:
            await ctx.send(f"You're already a member.")
        if count == 1:
            member = members[0]
            await ctx.send(f"`{member}` is now a member.")
        if count == 2:
            await ctx.send(f"`{members[0]}` and `{members[1]} `"
                           "are now members.")
        else:
            last_member = members[count - 1]
            members = members.pop(count - 1)
            string = "`"
            members = string + ", ".join(str(x) for x in members) + string
            members = members + f" and `{last_member}`"
            await ctx.send(f"{members} are now members of your project.")

    @commands.Cog.listener()
    async def on_project_member_add(self, guild_id: int, project: dict,
                                    members: list) -> discord.Message:
        """This fires when members are added."""
        # print(project)
        guild = (await self.bot.fetch_guild(guild_id))
        channel = await self.bot.fetch_channel(int(project.get("channel")))
        members = [(await guild.fetch_member(member)) for member in members]
        count = len(members)
        if count == 1:
            member = members[0]
            return await channel.send(f"**> Member Update:** `{member}` was"
                                      " added to this project.")
        if count == 2:
            return await channel.send(f"**> Member Update:** `{members[0]} `"
                                      f"and `{members[1]}"
                                      " were added to this project."
                                      )
        else:
            last_member = members[count - 1]
            members = members.pop(count - 1)
            string = "`"
            members = string + "`, ".join(str(x) for x in members) + string
            members = members + f" and `{last_member}`"
            return await channel.send(f"**> Member Update:** {members} were "
                                      "added to this project.")


def setup(bot):
    bot.add_cog(Projects(bot))
