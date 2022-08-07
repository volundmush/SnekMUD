import re
import snekmud

from .base import Command, ConnectionCommandHandler
from snekmud.exceptions import CommandError
from snekmud.db.accounts.models import Account


class ConnectionLoginCmdHandler(ConnectionCommandHandler):
    sub_categories = ["login"]


class _LoginCommand(Command):
    """
    Simple bit of logic added for the login commands to deal with syntax like:
    connect "user name" password
    """
    main_category = "connection"
    sub_categories = ["login"]

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
            raise CommandError(error)

        result = self.re_quoted.match(mdict["args"])
        if not result:
            result = self.re_unquoted.match(mdict["args"])
        rdict = result.groupdict()
        if not (rdict["name"] and rdict["password"]):
            raise CommandError(error)
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
        await self.connection.check_login(name, password)



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
        Account.objects.create_user(username=name, password=password)
        await self.send_line(text=f"User '{name}' created!")