import json
import logging
from collections import namedtuple

import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO)


class Bot(commands.AutoShardedBot):
    """An extension of AutoShardedBot, provided by the discord.py library"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        with open("./config.json", "r", encoding="utf8") as file:
            data = json.dumps(json.load(file))
            self.config = json.loads(data, object_hook=lambda d: namedtuple(
                "config", d.keys())(*d.values()))

    async def on_ready(self):
        self.load_extension('ui.developer')
        game = discord.Game("Unfinished.")
        await self.change_presence(status=discord.Status.dnd, activity=game)
        print("Running.")


flux = Bot(command_prefix=commands.when_mentioned_or("."))
