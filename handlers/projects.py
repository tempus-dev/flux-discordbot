import datetime

from core.bot import flux
from typing import Union


class ProjectHandler:
    """This manages the creation & deletion of projects."""
    
    def __init__(self, guild: int):
        self.guild = str(guild)
    
    async def create_project(self, owner: int, name: int, channel: int) -> dict:
        """This creates a project."""
        project = {
            "name": name,
            "tasks": [],
            "owner": owner,
            "channel": channel
        }
        guild_db = flux.db("guilds").find(self.guild)
        if guild_db is None:
            flux.db("guilds").insert(self.guild, {"projects": [project]})
        elif guild_db.get("projects") is None:
            flux.db("guilds").update(self.guild, {"projects": [project]})
        else:
            guild_db.get("projects").append(project)
            flux.db("guilds").update(self.guild, guild_db)
        
        flux.dispatch("project_created", name)
        return project

    async def find_project(self, name: str) -> dict:
        """This searches for a project within a given guild."""
        guild = flux.db("guilds").find(self.guild)
        projects = guild.get("projects")
        if not projects:
            return
        return next((item for item in projects if item["name"] == name), None)

    async def update_project_channel(self, project: str, channel: int) -> dict:
        """This updates the channel that contains the quick information display."""
        project = self.find_project(project)
        project["channel"] = channel
        flux.db("guilds").update(self.guild, project)
        return project

    async def project_completion(self, project: str) -> int:
        """This returns how close a project is to completion, out of 100."""
        guild = flux.db("guilds").find(self.guild)
        if guild is None or guild.get("projects") is None:
            return
        project = next((item for item in guild.get("projects") if item["name"] == project), None)
        if not project:
            return
        tasks = len(project.get('tasks'))
        if tasks == 0:
            return
        completed_tasks = len([item for item in project.get("tasks") if item.get("completed") == True])
        if completed_tasks == 0:
            return 0
        return round(completed_tasks/tasks*100)

    async def create_task(self, project: str, name: str, value: int, due: datetime.datetime) -> dict:
        """This creates a task within a project."""
        task = {
            "name": name,
            "start_timestamp": datetime.datetime.now(),
            "due_timestamp": due,
            "completed": False,
            "assigned": [],
            "value": value,
            "project": project
        }
        project = await self.find_project(project)
        project.get("tasks").append(task)
        flux.db("guilds").update(self.guild, project)
        flux.dispatch("task_created", name, value)
        return task

    async def find_task(self, project: str, task: str) -> dict:
        """This searches for a task within a given project, within a given guild."""
        project = self.find_project(project)
        task = next((item for item in project.get("tasks") if item["name"] == task), None)
        return task

    async def update_task_members(self, project: str, task: str, member: Union[int, list]) -> dict:
        """This assigns a member to a task."""
        task = self.find_task(project, task)
        if isinstance(member, list):
            task["members"].extend(member)
        else:
            task["members"].append(member)
        flux.db("guilds").update(project, task)
        flux.dispatch("task_member_update", task.get("name"), )
        return task

    async def update_task_value(self, project: str, task: str, value: int) -> dict:
        """This modifies the value of a task."""
        task = self.find_task(project, task)
        task["value"] += value
        flux.db("guilds").update(self.guild, task)

    async def update_task_status(self, project: str, task: str, status: bool) -> dict:
        """This marks a task as completed."""
        task = self.find_task(project, task)
        if task.get("completed") == status:
            return task
        task["completed"] = status
        flux.db("guilds").update(self.guild, task)
        if status:
            flux.dispatch("task_complete", self.guild, task)
        if not status:
            flux.dispatch("task_revoke", self.guild, task)
        return task


        