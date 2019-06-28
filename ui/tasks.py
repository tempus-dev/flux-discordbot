import re
import time
import datetime

from typing import Union

import discord

from discord.ext import commands

from handlers.projects import ProjectHandler
from handlers.points import Points


class Tasks(commands.Cog, name="Tasks"):
    """This manages tasks in a project."""

    def __init__(self, bot):
        self.bot = bot

    def parse_time(self, time: str) -> datetime.datetime:
        time = re.match(r"(?:(?P<weeks>\d+)w)?(?:\s+)?(?:(?P<days>\d+)d)?(?:\s+)?(?:(?P<hours>\d+)h)?(?:\s+)?(?:(?P<minutes>\d+)m)?(?:\s+)?(?:(?P<seconds>\d+)s)?", time)
        time = time.groupdict()
        for k, v in time.items():
            if time[k] is None:
                time[k] = 0
        for k, v in time.items():
            time[k] = int(v)
        time = datetime.timedelta(weeks=time.get("weeks"), days=time.get("days"), hours=time.get("hours"), minutes=time.get("minutes"), seconds=time.get("seconds"))
        time = datetime.datetime.now() + time
        return time

    @commands.group()
    async def tasks(self, ctx) -> None:
        """Task related commands."""
        pass

    @tasks.command()
    async def create(self, ctx, name: str, project: str, reward: int, *due) -> discord.Message:
        """This creates a task.
        
        This command is limited to the owner of the provided project."""
        projects = ProjectHandler(ctx.guild.id)
        if str(ctx.author.id) not in projects.find_project(project).get("owner"):
            return await ctx.send("You can't create tasks on this project.  o.o")
        due = " ".join(due)
        time = self.parse_time(due)
        projects.create_task(project, name, reward, time)
        return await ctx.send("Task created!")

    @tasks.command()
    async def assign(self, ctx, task: str, project: str, members: commands.Greedy[discord.Member]) -> discord.Message:
        """This assigns members to a project.
        
        This command is limited to the owner of the provided project."""
        projects = ProjectHandler(ctx.guild.id)
        if str(ctx.author.id) not in projects.find_project(project).get("owner"):
            return await ctx.send("You can't assign members to this task.  o.o")
        members = members if members > 0 else ctx.author
        count = len(members)
        projects.update_task_members(project, task, [x.id for x in members])
        if members == ctx.author:
            return await ctx.send(f"Successfully assigned you to `{task}`.")
        if count == 1:
            member = members[0]
            return await ctx.send(f"Assigned `{member}` to `{task}`.")
        if count == 2:
            return await ctx.send(f"Assigned `{members[0]}` and `{members[1]}` to `{task}`.")
        else:
            last_member = members[count - 1]
            members = members.pop(count - 1)
            string = "`"
            members = string + "`, ".join(str(x) for x in members) + string
            members = members + f" and `{last_member}`"
            return await ctx.send(f"Assigned {members} to `{task}`.")

    @tasks.command()
    async def complete(self, ctx, task: str, project: str) -> discord.Message:
        """This marks a task as complete.
        
        This command is limited to the owner of the provided project, and the members assigned to the provided task."""
        projects = ProjectHandler(ctx.guild.id)
        if str(ctx.author.id) not in projects.find_project(project).get("owner") and str(ctx.author.id) not in task.get("assigned"):
            return await ctx.send("You can't mark this task as complete.  o.o")
        projects.update_task_status(project, task, True)
        return await ctx.send(f"Marked `{task}` as completed!")

    @tasks.command()
    async def incomplete(self, ctx, task: str, project: str) -> discord.Message:
        """This marks a task as incomplete.
        
        This command is limited to the owner of the provided project, and the members assigned to the provided task."""
        projects = ProjectHandler(ctx.guild.id)
        if str(ctx.author.id) not in projects.find_project(project).get("owner") and str(ctx.author.id) not in task.get("assigned"):
            return await ctx.send("You can't mark this task as incomplete.  o.o")
        projects.update_task_status(project, task, False)
        return await ctx.send(f"Marked `{task}` as incomplete.")

    @commands.Cog.listener()
    async def on_task_member_update(self, task: dict, guild_id: int, members: list) -> discord.Message:
        """This sends a message when a member is added"""
        projects = ProjectHandler(guild_id)
        guild = discord.utils.get(self.bot.guilds, id=guild_id)
        project = projects.find_project(task.get("project"))
        channel = discord.utils.get(guild.channels, id=int(project.get("channel")))
        members = [discord.utils.get(guild.members, id=member) for member in members]
        count = len(members)
        if count == 1:
            member = members[0]
            return await channel.send(f"**> Member Update:** `{member}` was added to `{task}`.")
        if count == 2:
            return await channel.send(f"**> Member Update:** `{members[0]}` and `{members[1]}` were added to `{task}`.")
        else:
            last_member = members[count - 1]
            members = members.pop(count - 1)
            string = "`"
            members = string + "`, ".join(str(x) for x in members) + string
            members = members + f" and `{last_member}``"
            return await channel.send(f"**> Member Update:** {members} were added to `{task}`.")

    @commands.Cog.listener()
    async def on_task_create(self, guild_id: int, task: dict) -> discord.Message:
        """Sends a message on the creation of a task to the approporiate project channel."""
        projects = ProjectHandler(guild_id)
        guild = discord.utils.get(self.bot.guilds, id=guild_id)
        channel = discord.utils.get(guild.channels, id=projects.find_project(task.get("project")).get("channel"))
        task_name = task.get("name")
        task_reward = task.get("reward")
        return await channel.send(f"**> Task creation:** The task `{task_name}` was created. Bounty for completion: `{task_reward}` points!")

    @commands.Cog.listener()
    async def on_task_complete(self, guild_id: int, task: dict) -> discord.Message:
        """This event is fired on the completion of a task."""
        pointhandler = Points()
        value = task.get("value")
        start_timestamp = task.get("start_timestamp")
        end_timestamp = task.get("due")
        points = pointhandler.calculate_points(start_timestamp, end_timestamp, value)
        pointhandler.add_points(guild_id, task, points)

        projects = ProjectHandler(guild_id)
        guild = discord.utils.get(self.bot.guilds, id=guild_id)
        channel = discord.utils.get(guild.channels, id=projects.find_project(task.get("project")).get("channel"))
        task_name = task.get("name")
        task_reward = task.get("reward")
        message = await channel.fetch_message(int(projects.find_project(task.get("project")).get("message")))
        await message.edit(content=projects.project_progress_bar(task.get("projects")))
        return await channel.send(f"**> Task completion:** The task `{task_name}` was completed and the bounty of `{task_reward}` points has been claimed!")

    @commands.Cog.listener()
    async def on_task_revoke(self, guild_id: int, task: dict) -> discord.Message:
        """This is fired when someone marks a task as incomplete."""
        projects = ProjectHandler(guild_id)
        pointhandler = Points()
        all_logs = list(self.bot.db("logs").find_all())
        for member in task.get("assigned"):
            task_name = task.get("name")
            logs = list(filter(lambda all_logs: all_logs['name'] == f"point_addition_{member}_{task_name}"), all_logs)
            points_gained = [log.get("amount") for log in logs]
            for points in points_gained:
                pointhandler.remove_points(guild_id, task, points)

        guild = discord.utils.get(self.bot.guilds, id=guild_id)
        channel = discord.utils.get(guild.channels, id=projects.find_project(task.get("project")).get("channel"))
        task_name = task.get("name")
        task_reward = task.get("reward")
        return await channel.send(f"**> Task revoked:** The task `{task_name}` was marked as incomplete. The bounty of `{task_reward}` points is back up.")
        


                
        