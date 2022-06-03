import re
import snekmud

from snekmud.commands.base import Command, BaseCommandHandler, PyCommand

class AccountHandler(BaseCommandHandler):
    category = "connection_account"


class OOCPyCommand(PyCommand):

    @classmethod
    async def access(cls, entry):
        return entry.get_slevel() >= 10

    def available_vars(self):
        out = super().available_vars()
        out["account"] = self.entry.connection.user
        out["connection"] = self.entry
        if self.entry.connection.session:
            out.update(self.entry.connection.session.get_py_vars())

        return out


ACCOUNT_COMMANDS = [OOCPyCommand, ]