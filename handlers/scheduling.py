import asyncio
import datetime
from typing import Coroutine


class Scheduler:
    """ Schedules a callback function. """
    def __init__(self, duration: int, callback: Coroutine):
        self._duration = duration
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._duration)
        await self._callback

    def cancel(self):
        self._task.cancel()

    @classmethod
    def schedule(cls, end: float, callback: Coroutine):
        """ Schedules task using timestamp. """
        duration = datetime.datetime.fromtimestamp(end) - datetime.datetime.now()
        return cls(duration.seconds, callback)
