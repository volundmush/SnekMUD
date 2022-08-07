import re
import snekmud

from .base import Command, ConnectionCommandHandler
from snekmud.exceptions import CommandError
from snekmud.db.accounts.models import Account


class ConnectionSessionCmdHandler(ConnectionCommandHandler):
    sub_categories = ["session", "universal"]

    async def no_match(self, cmd: str):
        if self.owner.session:
            await self.owner.session.handler.process_input_text(cmd)
