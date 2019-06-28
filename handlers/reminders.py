from datetime import datetime, timedelta
from uuid import uuid4

from discord.ext import commands

from handlers.scheduling import Scheduler


class Reminder:
    def __init__(self, id, author_id, message, time):
        self.id = id
        self.author_id = author_id
        self.message = message
        self.time = time

    def serialize(self):
        return {
            'id': self.id,
            'author_id': self.author_id,
            'message': self.message,
            'time': self.time
        }

    def __repr__(self):
        return (f"<Reminder id={self.id} author_id={self.author_id}"
                f" message={self.message} time={self.time}>")


class ReminderService:
    def __init__(self, bot):
        self.bot = bot

    async def new_reminder(self, author_id, message, time):
        reminder = Reminder(str(uuid4()), str(author_id), message, time)
        print(reminder)
        data = reminder.serialize()
        name = data["id"]
        data.pop("id")
        self.bot.db("reminders").insert(name, data)
        await self._set_reminder(reminder)


    async def _set_reminder(self, reminder):
        async def remind(bot, reminder): 
            author = (await bot.fetch_user(reminder.author_id))
            await author.send(reminder.message)
            self.bot.db("reminders").delete(reminder.id)

        Scheduler(reminder.time, remind(self.bot, reminder))

    