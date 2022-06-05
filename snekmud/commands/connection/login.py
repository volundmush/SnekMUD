import re
import snekmud

from snekmud.commands.base import Command, BaseCommandHandler, CommandException


class LoginHandler(BaseCommandHandler):
    category = "connection_login"


class _LoginCommand(Command):
    """
    Simple bit of logic added for the login commands to deal with syntax like:
    connect "user name" password
    """

    re_quoted = re.compile(
        r'^"(?P<name>.+)"(: +(?P<password>.+)?)?', flags=re.IGNORECASE
    )
    re_unquoted = re.compile(
        r"^(?P<name>\S+)(?: +(?P<password>.+)?)?", flags=re.IGNORECASE
    )
    help_category = "Login"

    def parse_login(self, error):
        mdict = self.match_obj.groupdict()
        if not mdict["args"]:
            raise CommandException(error)

        result = self.re_quoted.match(mdict["args"])
        if not result:
            result = self.re_unquoted.match(mdict["args"])
        rdict = result.groupdict()
        if not (rdict["name"] and rdict["password"]):
            raise CommandException(error)
        return rdict["name"], rdict["password"]


class ConnectCommand(_LoginCommand):
    """
    Logs in to an existing User Account.
    Usage:
        connect <username> <password>
    If username contains spaces:
        connect "<user name>" <password>
    """

    name = "connect"
    re_match = re.compile(r"^(?P<cmd>connect)(?: +(?P<args>.+))?", flags=re.IGNORECASE)
    usage = (
        "Usage: "
        + "connect <username> <password>"
        + " or "
        + 'connect "<user name>" password'
    )

    async def execute(self):
        name, password = self.parse_login(self.usage)
        await self.user.check_login(name, password)


class CreateCommand(_LoginCommand):
    """
    Creates a new Account.
    Usage:
        create <username> <password>
    If username contains spaces:
        create "<user name>" <password>
    """

    name = "create"
    re_match = re.compile(r"^(?P<cmd>create)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)
    usage = (
        "Usage: "
        + "create <username> <password>"
        + " or "
        + 'create "<user name>" <password>'
    )

    async def execute(self):
        name, password = self.parse_login(self.usage)
        await snekmud.GAME.accounts.create(name, password, source=self.user)
        await self.user.msg(text=f"User '{name}' created!")


class ImportCommand(Command):
    name = "import"
    syntax = "import <path>"
    re_match = re.compile(r"^(?P<cmd>import)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    async def execute(self):
        if snekmud.ACCOUNTS:
            raise CommandException(f"This can only be used with an empty database!")
        from snekmud.profile_template.convert import GameImporter
        mdict = self.match_obj.groupdict()
        importer = GameImporter(mdict.get("args", "lib"))
        await importer.run()
        await self.entry.connection.msg(line="Import complete!", system_msg=True)


LOGIN_COMMANDS = [CreateCommand, ConnectCommand, ImportCommand]