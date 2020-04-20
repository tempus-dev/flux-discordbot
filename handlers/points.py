import datetime


from core.bot import flux


class Points:
    """Handles giving or talking points."""

    def add_points(self, guild_id: int, task: dict, points: int):
        guild = flux.db("guilds").find(str(guild_id))
        if guild.get("points") is None:
            guild["points"] = {}
            flux.db("guilds").update(str(guild_id), guild)

        for member in task.get("assigned"):
            member = str(member)
            if guild.get("points").get("member") is None:
                guild.get("points")[member] = points
                flux.db("guilds").update(str(guild_id), guild)
                task_name = task.get("name")
                flux.db("logs").insert(
                    f"point_addition_{member}_{task_name}",
                    {"time": datetime.datetime.now(), "amount": points}
                )
            else:
                guild.get("points")[member] = points
                flux.db("guilds").update(str(guild_id), guild)
                task_name = task.get("name")
                flux.db("logs").insert(
                    f"point_addition_{member}_{task_name}",
                    {"time": datetime.datetime.now(), "amount": points})

    def remove_points(self, guild_id: int, task: dict, points: int):
        guild = flux.db("guilds").find(str(guild_id))
        if guild.get("points") is None:
            guild["points"] = {}
            flux.db("guilds").update(str(guild_id), guild)

        for member in task.get("assigned"):
            member = str(member)
            if guild.get("points").get(member) is None:
                guild["points"][member] = points
                flux.db("guilds").update(str(guild_id), guild)
                task_name = task.get("name")
                points = points - points - points
                flux.db("logs").insert(
                    f"point_removal_{member}_{task_name}",
                    {"time": datetime.datetime.now(), "amount": points}
                )
            else:
                guild["points"][member] -= points
                flux.db("guilds").update(str(guild_id), guild)
                task_name = task.get("name")
                flux.db("logs").insert(
                    f"point_removal_{member}_{task_name}",
                    {"time": datetime.datetime.now(), "amount": points}
                )

    def calculate_points(self, start_timestamp, end_timestamp: float,
                         value: int):
        start = datetime.datetime.fromtimestamp(start_timestamp)
        end = datetime.datetime.fromtimestamp(end_timestamp)
        total_days = (end - start).days
        left_days = (end - datetime.datetime.now()).days

        bonus_points = round(((value / total_days) / 2) * left_days)
        return bonus_points + value
