import datetime

from core.bot import flux


class ProjectHandler:
    """This manages the creation & deletion of projects."""

    def __init__(self, guild: int):
        self.guild = str(guild)

    def generate_progress_bar(self, iter, total, prefix='', suffix='',
                              decimals=1, length=22, fill='\u2588'):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required : current iteration (Int)
            total       - Required : total iterations (Int)
            prefix      - Optional : prefix string (Str)
            suffix      - Optional : suffix string (Str)
            decimals    - Optional : positive # of decimals in % complete (Int)
            length      - Optional : character length of bar (Int)
            fill        - Optional : bar fill character (Str)
        """
        t = total
        percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                         (iter / float(t)))
        filledLength = int(length * iter // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        progress_bar = "\r%s |%s| %s%% %s" % (prefix, bar, percent, suffix)
        return progress_bar

    def create_project(self, owner: int, member: int, name: str, channel: int,
                       message: int) -> dict:
        """This creates a project."""
        project = {
            "name": name,
            "tasks": [],
            "owner": str(owner),
            "members": [str(member)],
            "channel": str(channel),
            "message": str(message),
            "number": None
        }
        guild_db = flux.db("guilds").find(self.guild)
        if not guild_db:
            project["number"] = 0
            flux.db("guilds").insert(self.guild, {"projects": [project]})
        elif not guild_db.get("projects"):
            project["number"] = 0
            flux.db("guilds").update(self.guild, {"projects": [project]})
        else:
            if self.find_project(name):
                return None
            project["number"] = len(guild_db.get("projects"))
            guild_db.get("projects").append(project)
            flux.db("guilds").update(self.guild, guild_db)

        flux.dispatch("project_created", name)
        return project

    def delete_project(self, name: str) -> None:
        """This deletes a project."""
        project = self.find_project(name)
        if not project:
            return
        guild = flux.db("guilds").find(self.guild)

        for i in range(len(guild.get("projects"))):
            if guild.get("projects")[i].get('name') == name:
                del guild['projects'][i]
                break
        flux.db("guilds").update(self.guild, guild)

    def find_project(self, name: str) -> dict:
        """This searches for a project within a given guild."""
        guild = flux.db("guilds").find(self.guild)
        if not guild:
            flux.db("guilds").insert(self.guild, {"projects": []})
            return
        projects = guild.get("projects")
        if not projects:
            return
        return next((item for item in projects if item["name"] == name), None)

    def update_project_channel(self, project: str, channel: int) -> dict:
        """This updates the channel that contains the information display."""
        project = self.find_project(project)
        project["channel"] = channel
        flux.db("guilds").update(self.guild, project)
        return project

    def project_completion(self, project: str) -> int:
        """This returns how close a project is to completion, out of 100."""
        guild = flux.db("guilds").find(self.guild)
        if (not guild) or (guild.get("projects")):
            return
        project = next((item for item in guild.get("projects")
                        if item["name"] == project), None)
        if not project:
            return
        tasks = len(project.get('tasks'))
        if tasks == 0:
            return
        completed_tasks = len([item for item in project.get(
            "tasks") if item.get("completed")])
        if completed_tasks == 0:
            return 0
        return round(completed_tasks/tasks*100)

    def project_progress_bar(self, project: str) -> int:
        """This returns how close a project is to completion, out of 100."""
        guild = flux.db("guilds").find(self.guild)
        if (not guild) or (guild.get("projects")):
            return
        project = next((item for item in guild.get("projects")
                        if item["name"] == project), None)
        if not project:
            return
        tasks = len(project.get('tasks'))
        if tasks == 0:
            return "Create a task to have a progress bar!"
        completed_tasks = len([item for item in project.get(
            "tasks") if item.get("completed")])
        # if completed_tasks == 0:
        #    return
        return self.generate_progress_bar(completed_tasks, tasks,
                                          prefix="Project Progress:",
                                          suffix="Complete")

    def add_project_members(self, project: str, members: list) -> dict:
        """This adds a project member to the member list."""
        guild_db = flux.db("guilds").find(self.guild)
        members = [str(member) for member in members]
        project = self.find_project(project)
        current_owners = project.get('members')
        current_owners.extend(members)
        guild_db["projects"][project.get("number")]["members"] = current_owners
        flux.db("guilds").update(self.guild, guild_db)

        flux.dispatch("project_member_add", self.guild, project, members)
        return project

    def create_task(self, project: str, name: str, value: int,
                    due: datetime.datetime) -> dict:
        """This creates a task within a project."""
        start_ = (datetime.datetime.now() + datetime.timedelta(minutes=0))
        task = {
            "name": name,
            "start_timestamp": start_,
            "end_timestamp": due,
            "completed": False,
            "assigned": [],
            "value": value,
            "project": project,
            "number": None
        }
        project = self.find_project(project)
        project.get("tasks").append(task)
        guild_db = flux.db("guilds").find(self.guild)
        number = len(guild_db["projects"][project.get("number")]["tasks"])
        task["number"] = number
        guild_db["projects"][project.get("number")]["tasks"].append(task)
        flux.db("guilds").update(self.guild, guild_db)
        flux.dispatch("task_create", self.guild, task)
        return task

    def find_task(self, project: str, task: str) -> dict:
        """This searches for a task within a given project,
        within a given guild."""
        project = self.find_project(project)
        task = next((item for item in project.get(
            "tasks") if item["name"] == task), None)
        return task

    def update_task_members(self, project: str, task: str,
                            member: list) -> dict:
        """This assigns a member to a task."""
        task = self.find_task(project, task)
        member = [str(x) for x in member]
        project = self.find_project(task.get("project"))
        guild_db = flux.db("guilds").find(self.guild)
        guild_db["projects"][project.get("number")]["tasks"][task.get(
            "number")]["assigned"].extend(member)
        flux.db("guilds").update(self.guild, guild_db)
        flux.dispatch("task_member_update", task, int(self.guild), member)
        return task

    def update_task_value(self, project: str, task: str, value: int) -> dict:
        """This modifies the value of a task."""
        task = self.find_task(project, task)
        guild_db = flux.db("guilds").find(self.guild)
        guild_db["projects"][project.get(
            "number")]["tasks"][task.get("number")]["value"] += value
        flux.db("guilds").update(self.guild, guild_db)

    def update_task_status(self, project: str, task: str,
                           status: bool) -> dict:
        """This marks a task as completed."""
        task = self.find_task(project, task)
        if task.get("completed") == status:
            return task
        if not task:
            return
        project = self.find_project(task.get("project"))
        if not project:
            return
        guild_db = flux.db("guilds").find(self.guild)
        i = 0
        for iteration in guild_db['projects']:
            i += 1
            if iteration['name'] == project['name']:
                print(iteration)
                break
        j = 0
        for iteration in project['tasks']:
            j += 1
            if iteration['name'] == task['name']:
                print(iteration)
                break
        print(f"i: {i} j: {j}")
        guild_db["projects"][i-1]["tasks"][j-1]["completed"] = status
        flux.db("guilds").update(self.guild, guild_db)
        if status is True:
            flux.dispatch("task_complete", self.guild, task)
        if status is False:
            print("Do you even get here?")
            flux.dispatch("task_revoke", self.guild, task)
        return task
