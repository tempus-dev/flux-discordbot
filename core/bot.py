import datetime
import json
import logging
import re
import sys
import traceback
from enum import Enum
from functools import wraps

import discord
from discord.ext import commands

from bson.json_util import dumps
from handlers.insights import Insights
from handlers.reminders import ReminderService
from pymongo import MongoClient
from recordclass import recordclass


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _ensure_database(func: callable):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.db_client:
            return None
        return func(self, *args, **kwargs)

    return wrapper


def parse_time(time_re: str) -> datetime.datetime:
    """Parses a human-made relative time into a datetime.datetime object

    Args:
        time_re (str): The time the human has given.

    Returns:
        One singular datetime.datetime object.

    Raises:
        None.

    """
    time_re = re.match(
        r"(?:(?P<weeks>\d+)w)?(?:\s+)?(?:(?P<days>\d+)d)?(?:\s+)?(?:(?P<hours>\d+)h)?(?:\s+)?(?:(?P<minutes>\d+)m)?(?:\s+)?(?:(?P<seconds>\d+)s)?", time_re)  # noqa: E501

    time_re = time_re.groupdict()

    for k, v in time_re.items():
        if not time_re[k]:
            time_re[k] = 0

    for k, v in time_re.items():
        time_re[k] = int(v)

    time_re = datetime.timedelta(
        weeks=time_re.get("weeks"),
        days=time_re.get("days"),
        hours=time_re.get("hours"),
        minutes=time_re.get("minutes"),
        seconds=time_re.get("seconds")
        )

    time_re = datetime.datetime.now() - time_re

    return time_re


class Mongo:
    """Simple wrapper around PyMongo."""

    def __init__(self, db_client, collection):
        self.db_client = db_client
        self.collection = getattr(
            self.db_client, collection
        ) if db_client is not None else None

    @_ensure_database
    def find(self, name, pretty=False):
        data = self.collection.find_one({"name": name})
        if pretty:
            return(dumps(data, sort_keys=True, indent=2))
        return data

    @_ensure_database
    def find_all(self, pretty=False) -> dict:
        """This returns all the documents in a given collection."""
        return self.collection.find({})

    @_ensure_database
    def insert(self, name, value):
        document = {"name": name}
        document.update(value)
        return (self.collection.insert_one(document))

    @_ensure_database
    def update(self, name, data):
        document = self.find(name)
        document.update(data)
        document["name"] = name
        return self.save(document)

    @_ensure_database
    def pop(self, name, key):
        document = self.find(name)
        document.pop(key, None)
        return self.save(document)

    @_ensure_database
    def delete(self, name):
        return (self.collection.delete_one({"name": name}))

    @_ensure_database
    def save(self, doc):
        return (self.collection.save(doc))


class Flags(Enum):
    EMPLOYEE = 1
    PARTNER = 2
    HYPESQUAD_EVENTS = 4
    BUG_HUNTER = 8
    HYPESQUAD_BRAVERY = 64
    HYPESQUAD_BRILLIANCE = 128
    HYPESQUAD_BALANCE = 256
    EARLY_SUPPORTER = 512
    BUG_HUNTER_TIER_TWO = 16384


class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(command_attrs={
            # This is the command.help string
            'help': 'Shows help about the bot, a command, or a category',
            # this is a custom attribute passed to the
            # help command - cooldown
            'cooldown': commands.Cooldown(
                    1, 3.0, commands.BucketType.member)})

    def get_command_signature(self, ctx, cmd):
        """Method to return a commands name and signature"""
        self.context = ctx
        signature = cmd.signature
        if not signature and not cmd.parent:  # checking if it has
            # no args and isn't
            # a subcommand
            return f'{self.clean_prefix}{cmd.name}'
        if signature and not cmd.parent:  # checking if it has
            # args and isn't a subcommand
            return f'{self.clean_prefix}{cmd.name} {signature}'
        if not signature and cmd.parent:  # checking if it has no
            # args and is a subcommand
            return f'{self.clean_prefix}{cmd.parent} {cmd.name} {signature}'
        else:  # else assume it has args a signature and is a subcommand
            return f'{self.clean_prefix}{cmd.parent} {cmd.name} {signature}'

    # this is a custom written method along with all the others below this
    @staticmethod
    def get_command_aliases(cmd):
        """Method to return a commands aliases"""
        if not cmd.aliases:  # check if it has any aliases
            return ''
        else:
            return 'command aliases are'
            f'[`{"` | `".join([alias for alias in cmd.aliases])}`]'

    @staticmethod
    def get_command_description(command):
        """Method to return a commands short doc/brief"""
        if not command.short_doc:  # check if it has any brief
            return 'There is no documentation for this command currently'
        else:
            return command.short_doc

    @staticmethod
    def get_command_help(command):
        """Method to return a commands full description/doc string"""
        if not command.help:  # check if it has any brief or doc string
            return 'There is no documentation for this command currently'
        else:
            return command.help


class Bot(commands.Bot):
    """An extension of the Bot class, provided by the discord.py library"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_exception = None
        self.reminders = None
        self.db_client = db_client
        self.config = config
        self.helpc = HelpCommand()
        self.logger = logger
        self.flags = Flags
        self.empty_guild = {
            "projects": [],
            "points": {},
            "prefix": [self.config.prefix],
            "project_category": None
        }

    def parse_time(self, time_re) -> datetime.datetime:
        return parse_time(time_re)

    async def send_cmd_help(self, ctx) -> None:
        msg = f"""```{self.helpc.get_command_signature(ctx, ctx.command)}

{self.helpc.get_command_help(ctx.command)}```"""
        await ctx.send(msg)

    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        ctx   : Context
        error : Exception"""
        if hasattr(ctx.command, 'on_error'):
            return
        ignored = (commands.CommandNotFound)
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send(f"{ctx.command} has been disabled.")

        elif isinstance(error, commands.MissingRequiredArgument):
            return await self.send_cmd_help(ctx)

        elif isinstance(error, commands.BadArgument):
            return await self.send_cmd_help(ctx)

        elif isinstance(error, commands.UserInputError):
            return await self.send_cmd_help(ctx)

        elif isinstance(error, discord.errors.Forbidden):
            return await ctx.send("I lack the required permissions "
                                  "to execute this command properly.")

        elif isinstance(error, commands.errors.CheckFailure):
            return

        else:
            log = ("Exception in command '{}'\n"
                   "".format(ctx.command.qualified_name))
            log += "".join(traceback.format_exception(type(error), error,
                                                      error.__traceback__))
            self._last_exception = log
            try:
                raise error
            except Exception:
                uuid = await Insights(self).log_cmd_error(ctx, log)
                if ctx.author.id in self.config.owners:
                    await ctx.send("DEBUG: This command silently errored. "
                                   f"ID: {uuid}")
                print('Ignoring exception in command {}:'
                      .format(ctx.command), file=sys.stderr)
                logger.warning(f"Error ID: {uuid}")
        traceback.print_exception(type(error), error, error.__traceback__,
                                  file=sys.stderr)

    def db(self, collection):
        return Mongo(self.db_client, collection)

    async def on_ready(self):
        try:
            self.config.contact_channel = (await self.fetch_channel(
                self.config.contact_channel_id))
        except discord.errors.NotFound:
            self.config.contact_channel = None
        except discord.errors.Forbidden:
            self.config.contact_channel = None
        game = discord.Game(f"{self.config.prefix}help for help!")
        await self.change_presence(status=discord.Status.idle, activity=game)
        self.reminders = ReminderService(self)
        defaults = ['handlers.insights', 'ui.developer', 'ui.general',
                    'ui.support', 'ui.projects', 'ui.tasks', ]
        extensions = defaults if self.db_client else ['handlers.insights',
                                                      'ui.developer',
                                                      'ui.general',
                                                      'ui.support']
        for i in extensions:
            try:
                self.load_extension(i)
            except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                continue
            except Exception as e:
                log = f"Exception in extension {i}\n"
                log += "".join(traceback.format_exception(type(e), e,
                                                          e.__traceback__))
                self._last_exception = log
                uuid = await Insights(self).log_error(log)
                print(f"An error occured while loading extension {i}:",
                      file=sys.stderr)
                logger.warning(f"Error ID: {uuid}")
                traceback.print_exception(type(e), e, e.__traceback__,
                                          file=sys.stderr)
        print("Ready.")

    async def on_resumed(self):
        game = discord.Game(f"{self.config.prefix}help for help!")
        await self.change_presence(status=discord.Status.idle, activity=game)
        print("Resumed.")


# Connects to MongoDB

with open("./config.json", "r", encoding="utf8") as file:
    data = json.dumps(json.load(file))
    config = json.loads(data, object_hook=lambda d: recordclass(
        "config", d.keys())(*d.values()))


db_client = MongoClient(config.uri)[config.db]
try:
    db_client.collection_names()
except Exception:
    db_client = None
    logger.warning(
        "MongoDB connection failed. There will be no MongoDB support.")


def _prefix_callable(bot, msg):
    base = [f'<@!{bot.user.id}> ', f'<@{bot.user.id}> ']

    try:
        db = Mongo(db_client, "guilds")
        guild_db = db.find(str(msg.guild.id))
        if not msg.guild:
            base.append(config.prefix)
        elif not guild_db:
            base.append(config.prefix)
        elif not guild_db.get("prefix"):
            base.append(config.prefix)
        else:
            base.extend(guild_db.get("prefix"))
    except Exception:
        # TODO: Call insights exception here.
        base.append(config.prefix)

    return base


flux = Bot(
    db_client=db_client,
    config=config,
    command_prefix=_prefix_callable,
    help_command=None
)
