import re
import snekmud
from snekmud import COMPONENTS, WORLD, OPERATIONS

from .base import Command, GameSessionCommandHandler
from snekmud.exceptions import CommandError
from snekmud.db.accounts.models import Account


class SessionPuppetCmdHandler(GameSessionCommandHandler):
    sub_categories = ["universal", "puppet"]

    async def no_match(self, cmd: str):
        if self.owner.puppet:
            if (comp := WORLD.try_component(self.owner.puppet, COMPONENTS["HasCmdHandler"])):
                await comp.process_input_text(cmd)

class _PuppetCommand(Command):
    sub_categories = ["puppet"]


class Look(_PuppetCommand):
    name = "look"

    async def execute(self):
        if not (room := await OPERATIONS["GetRoomLocation"](self.entity).execute()):
            raise CommandError("There is nothing to see here... wherever 'here' is.")
        self.send(line=await OPERATIONS["DisplayRoom"](self.entity, room).execute())