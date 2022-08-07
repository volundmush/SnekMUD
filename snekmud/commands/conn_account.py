import re
import snekmud

from .base import Command, ConnectionCommandHandler
from snekmud.exceptions import CommandError
from snekmud.db.accounts.models import Account


class ConnectionAccountCmdHandler(ConnectionCommandHandler):
    sub_categories = ["account", "universal"]


class _AccountCommand(Command):
    main_category = "connection"
    sub_categories = ["account"]


class Play(_AccountCommand):
    name = "play"

    async def execute(self):
        if not self.args:
            raise CommandError("Play who?")
        if not (self.connection and (acc := self.connection.account)):
            raise CommandError("Must be logged in to play a character!")
        if not (found := acc.characters.filter(name__iexact=self.args).first()):
            raise CommandError("That character is not on your account!")
        await self.connection.create_or_join_gamesession(found.id)