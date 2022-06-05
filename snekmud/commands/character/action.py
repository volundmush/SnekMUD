import re
import snekmud
from rich.text import Text
import logging

from snekmud.commands.base import Command, BaseCommandHandler, PyCommand, CommandEntry, CommandException
from snekmud.db.room import ExitDir
from snekmud.utils.comms import act, ActType


class ActionHandler(BaseCommandHandler):
    category = "character_action"

    async def update(self, current_tick: int):
        if self.owner.wait_cmd_ticks:
            self.owner.wait_cmd_ticks -= 1
        if self.owner.wait_cmd_ticks == 0 and self.pending_command_queue:
            pending_command = self.pending_command_queue.pop(0)
            await self.parse(pending_command)


class Go(Command):
    name = "go"
    re_match = re.compile(r"^(?P<go>go )?(?P<cmd>n|north|e|east|s|south|w|west|u|up|d|down|nw|northwest|ne|northeast|se|southeast|sw|southwest|i|in|o|out)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    @classmethod
    async def access(cls, entry: CommandEntry):
        return entry.session.puppet.location is not None

    async def execute(self):
        mdict = self.match_obj.groupdict()
        cmd = mdict.get("cmd")
        if (dir := ExitDir.find(cmd)) == ExitDir.UNKNOWN:
            raise CommandException("That is not a valid direction! Contact a coder!")
        puppet = self.entry.session.puppet
        loc = puppet.location
        logging.info(f"EXITS ARE: {loc.exits}")
        if not (found := loc.exits.get(dir, None)):
            await puppet.msg(line=f"You can't find a way to go {dir.name.capitalize()}.", system_msg=True)
            return
        if not await found.visible_to(puppet):
            await puppet.msg(line=f"You can't find a way to go {dir.name.capitalize()}.", system_msg=True)
            return
        can, err = await found.can_traverse(puppet)
        if not can:
            await puppet.msg(line=err, system_msg=True)
            return
        can, err = await puppet.can_move_to(found.destination)
        if not can:
            await puppet.msg(line=err, system_msg=True)
            return
        await puppet.move_to(found.destination, via_exit=found)
        await act(msg=f"$n arrives from {dir.describe_move()}.", actor=puppet, act_type=ActType.TO_ROOM)


class Look(Command):
    name = "look"
    re_match = re.compile(r"^(?P<cmd>look|l)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    async def execute(self):
        character = self.entry.character
        rendered = await character.render_room(character.location)
        await character.msg(line=rendered, system_msg=True)


class Goto(Command):
    name = "goto"
    syntax = "goto <room vnum>"
    re_match = re.compile(r"^(?P<cmd>goto)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    @classmethod
    async def access(cls, entry: CommandEntry):
        return entry.get_slevel() > 0

    async def execute(self):
        character = self.entry.character
        mdict = self.match_obj.groupdict()
        if not (args := mdict.get("args", None)):
            raise CommandException("Must include a room vnum!")
        try:
            vnum = int(args)
        except ValueError:
            raise CommandException(f"Cannot convert {args} to a number.")
        if not (room := snekmud.ROOMS.get(vnum, None)):
            raise CommandException(f"Room {vnum} not found.")
        old_loc = character.location
        if old_loc:
            await act(msg=f"$n disappears in a puff of smoke.", actor=character, act_type=ActType.TO_ROOM)
        await character.do_move(destination=room)
        rendered = await character.render_room(character.location)
        await character.msg(line=rendered, system_msg=True)
        await act(msg=f"$n appears with a loud bang.", actor=character, act_type=ActType.TO_ROOM)


class At(Command):
    name = "at"
    syntax = "at <room vnum> <command>"
    re_match = re.compile(r"^(?P<cmd>at)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    @classmethod
    async def access(cls, entry: CommandEntry):
        return entry.get_slevel() > 0

    async def execute(self):
        character = self.entry.character
        location = character.location
        mdict = self.match_obj.groupdict()
        args = mdict.get("args", '')
        if not args:
            raise CommandException("Must include a room vnum!")
        if ' ' not in args:
            raise CommandException("Must include a room vnum and command!")
        vnum, cmd = args.split(' ', 1)
        try:
            vnum = int(vnum)
        except ValueError:
            raise CommandException(f"{vnum} is not a number!")
        if not (found := snekmud.ROOMS.get(vnum, None)):
            raise CommandException(f"Room {vnum} does not exist.")
        if not cmd:
            raise CommandException("Must include a room vnum and command!")

        entry = CommandEntry(cmd)
        entry.connection = self.entry.connection
        entry.session = self.entry.session
        entry.character = character

        # Okay here's where the magic happens.
        character.location = found
        if (c := await character.cmd_handler.get_match(entry)):
            await character.cmd_handler.found_match(entry, c[0], c[1])
        else:
            await character.msg(line="No command match.", system_msg=True)
        character.location = location



ACTION_COMMANDS = [Go, Look, Goto, At]
