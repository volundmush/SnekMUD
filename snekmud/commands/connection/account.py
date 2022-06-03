import re
import snekmud
from rich.text import Text

from snekmud.commands.base import Command, BaseCommandHandler, PyCommand, CommandEntry

class AccountHandler(BaseCommandHandler):
    category = "connection_account"


class SessionHandler(BaseCommandHandler):
    category = "connection_session"


class OOCPyCommand(PyCommand):

    @classmethod
    async def access(cls, entry):
        return entry.get_slevel() >= 10

    def available_vars(self):
        out = super().available_vars()
        out["account"] = self.entry.connection.user
        out["connection"] = self.entry.connection
        out["session"] = self.entry.connection.session
        if self.entry.connection.session:
            out.update(self.entry.connection.session.get_py_vars())

        return out


class FLevel(Command):
    name = "@flevel"
    syntax = "@flevel <level>"
    re_match = re.compile(r"^(?P<cmd>@flevel)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    @classmethod
    async def access(cls, entry: CommandEntry):
        return entry.get_slevel(ignore_spoof=True) > 0

    async def execute(self):
        mdict = self.match_obj.groupdict()
        acc = self.entry.connection.user
        args = mdict.get("args", None)

        true_level = acc.account.supervisor_level
        if not args:
            await self.entry.connection.msg(line=Text(f"Current @flevel: {self.entry.connection.fake_slevel}/{true_level}."))
            return
        try:
            val = int(args)
        except ValueError as err:
            raise ValueError(f"Could not parse '{args}' to an integer.")

        if val < 0 or val > true_level:
            raise ValueError(f"Cannot set @flevel lower than 0 or higher than your true level of {true_level}.")
        self.entry.connection.fake_slevel = val
        await self.entry.connection.msg(line=Text(f"@flevel set to: {val}/{true_level}"))

ACCOUNT_COMMANDS = [OOCPyCommand, FLevel]
