import datetime

import discord

from discord.ext import commands

from handlers.projects import ProjectHandler
from handlers.points import Points
from handlers.scheduling import Scheduler


class Tasks(commands.Cog, name="Tasks"):
    """This manages tasks in a project."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(hidden=True)
    async def tasks(self, ctx) -> None:
        """Task related commands."""
        ctx.projects = ProjectHandler(ctx.guild.id)

    @tasks.command()
    async def create(
        self,
        ctx,
        name: str,
        project: str,
        points_gained_when_completed: int,
        *,
        due: str,
    ) -> None:
        """This creates a task.
        This command is limited to the owner of the provided project."""
        reward = points_gained_when_completed  # Helpful params!
        if not ctx.projects.find_project(project):
            await ctx.send("This project could not be found.")
            return
        if str(ctx.author.id) not in ctx.projects.find_project(project).get("owner"):
            await ctx.send("You can't create tasks on this project.")
            return
        due = "".join(due)
        due = ctx.bot.parse_time(due)
        task = ctx.projects.create_task(project, name, reward, due)
        total_seconds = (datetime.datetime.now() - due).seconds

        async def _call_event():
            return ctx.bot.dispatch("task_due", ctx.guild.id, task)

        Scheduler(total_seconds, _call_event())
        ctx.projects.update_task_members(
            project, task.get("name"), [str(ctx.author.id)]
        )
        await ctx.send("Task created!")
        return

    @tasks.command()
    async def assign(
        self, ctx, task: str, project: str, members: commands.Greedy[discord.Member]
    ) -> None:
        """This assigns members to a project.
        This command is limited to the owner of the provided project."""
        if not ctx.projects.find_project(project):
            await ctx.send("I couldn't find this project.")
            return
        if str(ctx.author.id) not in ctx.projects.find_project(project).get("owner"):
            await ctx.send("You can't assign members to this task.")
            return
        task_dict = ctx.projects.find_task(project, task)
        if not task_dict:
            await ctx.end("This task does not exist.")
            return
        members = members if len(members) > 0 else [ctx.author]
        count = len(members)
        ctx.projects.update_task_members(project, task, [x.id for x in members])
        if members == ctx.author:
            await ctx.send(f"Successfully assigned you to `{task}`.")
            return
        if count == 1:
            member = members[0]
            await ctx.send(f"Assigned `{member}` to `{task}`.")
            return
        if count == 2:
            await ctx.send(
                f"Assigned `{members[0]}` and `{members[1]}` " f"to `{task}`."
            )
            return
        else:
            last_member = members[count - 1]
            members = members.pop(count - 1)
            string = "`"
            members = string + "`, ".join(str(x) for x in members) + string
            members = members + f" and `{last_member}`"
            await ctx.send(f"Assigned {members} to `{task}`.")
            return

    @tasks.command()
    async def complete(self, ctx, task: str, project: str) -> None:
        """This marks a task as complete.

        This command is limited to the owner of the provided project,
        and the members assigned to the provided task."""

        task = ctx.projects.find_task(project, task)
        if not task:
            await ctx.send("This task does not exist.")
            return

        if str(ctx.author.id) not in ctx.projects.find_project(project).get(
            "owner"
        ) and str(ctx.author.id) not in task.get("assigned"):
            await ctx.send(
                "You weren't assigned to this task."
                " Request the project owner to assign"
                " you to change it's status."
            )
            return

        task = ctx.projects.update_task_status(project, task.get("name"), True)
        name = task.get("name")
        await ctx.send(f"Task `{name}` is now completed!")
        return

    @tasks.command()
    async def incomplete(self, ctx, task: str, project: str) -> None:
        """This marks a task as incomplete.

        This command is limited to the owner of the provided project,
        and the members assigned to the provided task."""
        task = ctx.projects.find_task(project, task)
        if not task:
            await ctx.send("This task does not exist.")
            return

        if str(ctx.author.id) not in ctx.projects.find_project(project).get(
            "owner"
        ) and str(ctx.author.id) not in task.get("assigned"):
            await ctx.send(
                "You weren't assigned to this task."
                " Request the project owner to assign"
                " you to change it's status."
            )
            return

        task = ctx.projects.update_task_status(project, task.get("name"), False)
        name = task.get("name")
        await ctx.send(f"Task `{name}` is pending again. Bounty restored.")

        return

    @commands.Cog.listener()
    async def on_task_member_update(
        self, task: dict, guild_id: int, members: list
    ) -> None:
        """This sends a message when a member is added"""
        projects = ProjectHandler(guild_id)
        project = projects.find_project(task.get("project"))
        guild = await self.bot.fetch_guild(guild_id)
        channel = await self.bot.fetch_channel(int(project.get("channel")))
        members = [(await guild.fetch_member(member)) for member in members]
        count = len(members)
        task_name = task.get("name")
        if count == 1:
            member = members[0]
            return await channel.send(
                f"**> Member Update:** `{member}` " f"was added to `{task_name}`."
            )
        if count == 2:
            return await channel.send(
                f"**> Member Update:** `{members[0]}` "
                f"and `{members[1]}` were added "
                f"to `{task_name}`."
            )
        else:
            last_member = members[count - 1]
            members = members.pop(count - 1)
            string = "`"
            members = string + "`, ".join(str(x) for x in members) + string
            members = members + f" and `{last_member}``"
            return await channel.send(
                f"**> Member Update:** {members}" f" were added to `{task_name}`."
            )

    @commands.Cog.listener()
    async def on_task_create(self, guild_id: int, task: dict) -> None:
        """Sends a message on the creation of a task to the project channel."""
        projects = ProjectHandler(guild_id)
        project = projects.find_project(task.get("project"))
        channel = await self.bot.fetch_channel(int(project.get("channel")))
        task_name = task.get("name")
        task_reward = task.get("value")
        message = await channel.fetch_message(
            int(projects.find_project(task.get("project")).get("message"))
        )
        await message.edit(content=projects.project_progress_bar(task.get("project")))
        await channel.send(
            f"**> Task creation:** The task `{task_name}` "
            "was created. Bounty for completion: "
            f"`{task_reward}` points!"
        )

    @commands.Cog.listener()
    async def on_task_complete(self, guild_id: int, task: dict) -> None:
        """This event is fired on the completion of a task."""
        pointhandler = Points()
        projects = ProjectHandler(guild_id)
        project = projects.find_project(task.get("project"))
        value = (
            self.bot.db("guilds")
            .find(guild_id)
            .get("projects")[project.get("number")]
            .get("tasks")[task.get("number")]["value"]
        )
        # start_timestamp = (datetime.datetime.now() -
        #                 task.get("start_timestamp")).total_seconds()
        # end_timestamp = (task.get("end_timestamp") -
        #                datetime.datetime.now()).total_seconds()
        pointhandler.add_points(guild_id, task, value)

        channel = await self.bot.fetch_channel(int(project.get("channel")))
        task_name = task.get("name")
        value = (
            self.bot.db("guilds")
            .find(guild_id)
            .get("projects")[project.get("number")]
            .get("tasks")[task.get("number")]["value"]
        )
        message = await channel.fetch_message(
            int(projects.find_project(task.get("project")).get("message"))
        )
        await message.edit(content=projects.project_progress_bar(task.get("project")))
        return await channel.send(
            f"**> Task completion:** The task "
            f"`{task_name}` was completed and "
            f" the bounty of `{value}` "
            "points has been claimed!"
        )

    @commands.Cog.listener()
    async def on_task_revoke(self, guild_id: int, task: dict) -> None:
        """This is fired when someone marks a task as incomplete."""
        projects = ProjectHandler(guild_id)
        pointhandler = Points()
        all_logs = list(self.bot.db("logs").find_all())
        for member in task.get("assigned"):
            task_name = task.get("name")
            logs = list(
                filter(
                    lambda all_logs: all_logs["name"]
                    == f"point_addition_{member}_{task_name}",
                    all_logs,
                )
            )
            points_gained = [log.get("amount") for log in logs]
            for points in points_gained:
                pointhandler.remove_points(guild_id, task, points)

        project = projects.find_project(task.get("project"))
        channel = await self.bot.fetch_channel(int(project.get("channel")))
        task_name = task.get("name")
        task_reward = (
            self.bot.db("guilds")
            .find(guild_id)
            .get("projects")[project.get("number")]
            .get("tasks")[task.get("number")]["value"]
        )
        message = await channel.fetch_message(
            int(projects.find_project(task.get("project")).get("message"))
        )
        await message.edit(content=projects.project_progress_bar(task.get("project")))
        return await channel.send(
            f"**> Task revoked:** The task `{task_name}`"
            " was marked as incomplete. "
            f"The bounty of `{task_reward}` "
            "points is back up."
        )

    @commands.Cog.listener()
    async def on_task_due(self, guild_id: int, task: dict):
        """This fires when a task is due."""
        projects = ProjectHandler(guild_id)
        project = projects.find_project(task.get("project"))
        completed = (
            self.bot.db("guilds")
            .find(str(guild_id))
            .get("projects")[project.get("number")]
            .get("tasks")[task.get("number")]
            .get("completed")
        )
        if completed:
            return
        channel = await self.bot.fetch_channel(int(project.get("channel")))
        members = (
            self.bot.db("guilds")
            .find(str(guild_id))
            .get("projects")[project.get("number")]
            .get("tasks")[task.get("number")]
            .get("assigned")
        )
        members = [(await self.bot.fetch_user(member)) for member in members]
        new_value = task.get("value") * 10 / 100
        if new_value < 1:
            new_value = 1
        guild = self.bot.db("guilds").find(str(guild_id))
        guild.get("projects")[project.get("number")].get("tasks")[task.get("number")][
            "value"
        ] = new_value
        self.bot.db("guilds").update(str(guild_id), guild)
        task = guild.get("projects")[project.get("number")].get("tasks")[
            task.get("number")
        ]
        task_name = task.get("name")
        task_value = task.get("value")
        await channel.send(
            f"**> Task bounty update:** Task `{task_name}` "
            f"is now valued at `{task_value}` points."
        )
        for member in members:
            await member.send(
                f":alarm_clock: The task {task_name}"
                " is now overdue. And as such, the bounty is "
                "10% of what it originally was."
                f" Bounty now: `{task_value}` points."
            )


def setup(bot):
    bot.add_cog(Tasks(bot))
