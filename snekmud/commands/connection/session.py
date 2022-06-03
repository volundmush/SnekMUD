import re
import snekmud
from rich.text import Text

from snekmud.commands.base import Command, BaseCommandHandler, PyCommand, CommandEntry


class SessionHandler(BaseCommandHandler):
    category = "connection_session"

    async def no_match(self, cmd: CommandEntry):
        await self.owner.session.process_command_entry(cmd)



class LogoutCommand(Command):
    name = "@exit"
    syntax = "@exit"
    re_match = re.compile(r"^(?P<cmd>@exit)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    async def execute(self):
        mdict = self.match_obj.groupdict()
        force = mdict.get("args", '').lower() == "force"
        await self.entry.session.request_logout(force=force)

SESSION_COMMANDS = []