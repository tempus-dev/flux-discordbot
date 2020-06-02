import itertools
import inspect
from discord.ext.commands.core import GroupMixin, Command
from discord.ext.commands.errors import CommandError
from discord.ext.commands.help import Paginator


class HelpFormatter:
    """The default base implementation that handles formatting of the help
    command.
    To override the behaviour of the formatter, :meth:`~.HelpFormatter.format`
    should be overridden. A number of utility functions are provided for use
    inside that method.
    """

    def __init__(self, show_hidden=False, show_check_failure=False, width=80):
        self.width = width
        self.show_hidden = show_hidden
        self.show_check_failure = show_check_failure

    def has_subcommands(self):
        """Specifies if the command has subcommands."""
        return isinstance(self.command, GroupMixin)

    def is_bot(self):
        """Specifies if the command being formatted is the bot itself."""
        return self.command is self.context.bot

    def is_cog(self):
        """Specifies if the command being formatted is actually a cog."""
        return not self.is_bot() and not isinstance(self.command, Command)

    def shorten(self, text):
        """Shortens text to fit into the :attr:`width`."""
        if len(text) > self.width:
            return text[: self.width - 3] + "..."
        return text

    @property
    def max_name_size(self):
        """Returns the largest name length of a command or if it has subcommands
        the largest subcommand name."""
        try:
            commands = (
                self.command.all_commands
                if not self.is_cog()
                else self.context.bot.all_commands
            )
            if commands:
                m = max(
                    map(
                        lambda c: len(c.name)
                        if self.show_hidden or not c.hidden
                        else 0,
                        commands.values(),
                    )
                )
                return m
            return 0
        except AttributeError:
            return len(self.command.name)

    @property
    def clean_prefix(self):
        """The cleaned up invoke prefix.

        i.e. mentions are ``@name`` instead of ``<@id>``."""
        user = self.context.bot.user
        # this breaks if the prefix mention is not the bot itself but I
        # consider this to be an *incredibly* strange use case. I'd rather go
        # for this common use case rather than waste performance for the
        # odd one.
        clean_prefix = self.context.prefix.replace("!", "")
        clean_prefix = clean_prefix.replace(user.mention, "@" + user.name)
        return clean_prefix

    def get_command_signature(self):
        """Retrieves the signature portion of the help page."""
        prefix = self.clean_prefix
        cmd = self.command
        return prefix + cmd.signature

    def get_ending_note(self):
        command_name = self.context.invoked_with
        return (
            "Type {0}{1} command for more info on a command.\n"
            "You can also type {0}{1} category for more info on a category.".format(  # noqa: E501
                self.clean_prefix, command_name
            )
        )

    async def filter_command_list(self):
        """Returns a filtered list of commands based on the two attributes
        provided, `show_check_failure` and `show_hidden`.
        Also filters based on if `HelpFormatter.is_cog` is valid.
        """

        def sane_no_suspension_point_predicate(tup):
            cmd = tup[1]
            if self.is_cog():
                # filter commands that don't exist to this cog.
                if cmd.instance is not self.command:
                    return False

            if cmd.hidden and not self.show_hidden:
                return False

            return True

        async def predicate(tup):
            if sane_no_suspension_point_predicate(tup) is False:
                return False

            cmd = tup[1]
            try:
                return await cmd.can_run(self.context)
            except CommandError:
                return False

        iterator = (
            self.command.all_commands.items()
            if not self.is_cog()
            else self.context.bot.all_commands.items()
        )
        if self.show_check_failure:
            return filter(sane_no_suspension_point_predicate, iterator)

        # Gotta run every check and verify it
        ret = []
        for elem in iterator:
            valid = await predicate(elem)
            if valid:
                ret.append(elem)

        return ret

    def _add_subcommands_to_page(self, max_width, commands):
        for name, command in commands:
            if name in command.aliases:
                # skip aliases
                continue

            entry = "  {0:<{width}} {1}".format(
                name, command.short_doc, width=max_width
            )
            shortened = self.shorten(entry)
            self._paginator.add_line(shortened)

    async def format_help_for(self, context, command_or_bot):
        """Formats the help page and handles the actual heavy lifting of how
        the help command looks like. To change the behaviour, override the
        `HelpFormatter.format` method.
        """
        self.context = context
        self.command = command_or_bot
        return await self.format()

    async def format(self):
        """Handles the actual behaviour involved with formatting.
        To change the behaviour, this method should be overridden.
        """
        self._paginator = Paginator(prefix="", suffix="")

        # we need a padding of ~80 or so

        description = (
            self.command.description
            if not self.is_cog()
            else inspect.getdoc(self.command)
        )

        if description:
            # <description> portion
            self._paginator.add_line(description, empty=True)

        if isinstance(self.command, Command):

            # <long doc> section
            if self.command.help:
                self._paginator.add_line(self.command.help, empty=True)

            # end it here if it's just a regular command
            if not self.has_subcommands():
                self._paginator.close_page()
                return self._paginator.pages

        max_width = self.max_name_size

        def category(tup):
            cog = tup[1].cog_name
            # we insert the zero width space there to give it approximate
            # last place sorting position.
            return cog + ":" if cog is not None else "\u200bNo Category:"

        filtered = await self.filter_command_list()
        if self.is_bot():
            data = sorted(filtered, key=category)
            for category, commands in itertools.groupby(data, key=category):
                # there simply is no prettier way of doing this.
                commands = sorted(commands)
                if len(commands) > 0:
                    self._paginator.add_line(category)

                self._add_subcommands_to_page(max_width, commands)
        else:
            filtered = sorted(filtered)
            if filtered:
                self._add_subcommands_to_page(max_width, filtered)

        # add the ending note
        self._paginator.add_line()
        return self._paginator.pages
