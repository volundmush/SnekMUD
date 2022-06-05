import re
import snekmud
from rich.text import Text

from snekmud.commands.base import Command, BaseCommandHandler, PyCommand, CommandEntry


class CharacterHandler(BaseCommandHandler):
    category = "session_character"

    async def no_match(self, cmd: CommandEntry):
        await self.owner.puppet.process_command_entry(cmd)



CHARACTER_COMMANDS = []