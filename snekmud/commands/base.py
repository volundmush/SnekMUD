from typing import List, Optional, Union, Tuple
import snekmud
from mudforge.utils import lazy_property
import mudforge
from mudrich.evennia import EvenniaToRich
from mudrich.circle import CircleToRich


class Command:
    name = None  # Name must be set to a string!
    aliases = []
    help_category = None
    priority = 0
    min_text = None
    main_category = None
    sub_categories = []

    @classmethod
    async def access(cls, user: "HasCommandHandler") -> bool:
        """
        This returns true if <enactor> is able to see and use this command.
        Use this for admin permissions locks as well as conditional access, such as
        'is the enactor currently in a certain kind of location'.
        """
        return True

    @classmethod
    async def help(cls, user: "HasCommandHandler"):
        """
        This is called by the command-help system if help is called on this command.
        """
        pass

    @classmethod
    async def match(cls, match_obj, partial: bool = False, **kwargs):
        """
        Called by the CommandGroup to determine if this command matches.
        Returns False or a Regex Match object.
        Or any kind of match, really. The parsed match will be returned and re-used by .execute()
        so use whatever you want.
        """
        g_dict = match_obj.groupdict()
        cmd = g_dict.get("cmd")
        clower = cmd.lower()
        nlower = cls.name.lower()
        if clower == nlower:
            return cls(match_obj, **kwargs)
        for x in cls.aliases:
            if clower == x.lower():
                return cls(match_obj, **kwargs)
        if partial and cls.min_text:
            if nlower.startswith(clower) and clower.startswith(cls.min_text.lower()):
                return cls(match_obj, **kwargs)
        return None

    def __init__(self, handler, match_obj, **kwargs):
        """
        Instantiates the command.
        """
        self.handler = handler
        self.match_obj = match_obj
        self.__dict__.update(kwargs)
        self.__dict__.update(match_obj.groupdict())
        self.parse()

    def parse(self):
        pass

    async def at_pre_execute(self):
        pass

    async def execute(self):
        pass

    async def at_post_execute(self):
        pass

    def send_text(self, s: str):
        self.handler.send_text(s)

    def send_line(self, s: str):
        self.handler.send_line(s)

    def send(self, s: str):
        self.handler.send_line(s)

    def send_ev(self, s: str):
        self.handler.send_ev(s)

    def send_circle(self, s: str):
        self.handler.send_circle(s)


class HasCommandHandler:

    async def set_cmd_handler(self, handler_class, **kwargs):
        if self.cmd_handler:
            await self.cmd_handler.cleanup()
        self.cmd_handler = handler_class(self, **kwargs)
        await self.cmd_handler.start()


class BaseCommandHandler:
    main_category = None
    sub_categories = []
    partial_normal = True
    partial_special = False

    def __init__(self, owner, **kwargs):
        self.owner = owner
        self.pending_command_queue = list()
        self.normal_commands = None

    async def start(self):
        pass

    async def close(self):
        pass

    async def generate_kwargs(self):
        return dict()

    async def get_special_commands(self) -> List["Command_Class"]:
        return list()

    async def special_match(self, cmd: str, **kwargs) -> Optional["Command"]:
        for c in await self.get_special_commands():
            if (cmd := await c.match(cmd, partial=self.partial_special, **kwargs)):
                return cmd

    async def parse(self, cmd: str):
        kwargs = await self.generate_kwargs()
        if not (c := await self.special_match(cmd, **kwargs)):
            c = await self.normal_match(cmd, **kwargs)

        if c:
            await self.found_match(c)
        else:
            await self.no_match(cmd)

    async def no_match(self, cmd: str):
        await self.owner.msg(line=f"No command for: {cmd if len(cmd) < 20 else cmd[0:20] + '...'}. Type 'help' for help!")

    async def normal_match(self, cmd: str, **kwargs) -> Optional["Command"]:
        for c in await self.get_commands():
            if (cmd := await c.match(self.owner, cmd, partial=self.partial_normal, **kwargs)):
                return cmd

    async def found_match(self, cmd):
        try:
            await cmd.execute()
        except ValueError as err:
            await self.owner.msg(text=str(err), system_msg=True)

    async def cleanup(self):
        pass

    async def get_commands(self) -> List["Command_Class"]:
        if self.normal_commands is None:
            self.normal_commands = list()
            for sub in self.sub_categories:
                self.normal_commands.extend(snekmud.COMMANDS[self.main_category][sub])
            self.normal_commands.sort(key=lambda x: x.priority)
        return self.normal_commands

    async def update(self):
        """
        This is called every tick.
        Presumably used to process pending commands.
        """

    def send_line(self, s: str):
        self.owner.send_line(s)

    def send_text(self, s: str):
        self.owner.send_text(s)

    def send(self, s: str):
        self.send_line(s)

    def send_ev(self, s):
        self.owner.send_line(EvenniaToRich(s))

    def send_circle(self, s):
        self.owner.send_line(CircleToRich(s))


class ConnectionCommandHandler(BaseCommandHandler):
    main_category = "connection"

    async def generate_kwargs(self):
        out = {"connection": self.owner}
        if self.owner.account:
            out["account"] = self.owner.account
        return out

class GameSessionCommandHandler(BaseCommandHandler):
    main_category = "session"

    async def generate_kwargs(self):
        return {"session": self.owner,
                "character": self.owner.character,
                "entity": self.owner.puppet}

class EntityCommandHandler(BaseCommandHandler):
    main_category = "entity"

    async def generate_kwargs(self):
        return {"entity": self.owner.entity}