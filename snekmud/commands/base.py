from typing import List, Optional, Dict, Set, Union, Tuple
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum
import snekmud


class Command:
    name = None  # Name must be set to a string!
    aliases = []
    help_category = None

    @classmethod
    async def access(cls, user: "HasCommandHandler"):
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
    async def match(cls, user: "HasCommandHandler", text: str):
        """
        Called by the CommandGroup to determine if this command matches.
        Returns False or a Regex Match object.
        Or any kind of match, really. The parsed match will be returned and re-used by .execute()
        so use whatever you want.
        """
        return cls.re_match.fullmatch(text)

    def __init__(self, user: "HasCommandHandler", text: str, match_obj):
        """
        Instantiates the command.
        """
        self.text = text
        self.match_obj = match_obj
        self.user: Union["Connection", "Session", "Mobile"] = user

    async def execute(self):
        pass


class HasCommandHandler:

    async def set_cmd_handler(self, handler_class, **kwargs):
        if self.cmd_handler:
            await self.cmd_handler.cleanup()
        self.cmd_handler = handler_class(self, **kwargs)
        await self.cmd_handler.start()


class BaseCommandHandler:
    category = ""

    def __init__(self, owner: HasCommandHandler, **kwargs):
        self.owner = owner
        self.pending_command_queue = list()
        self.__dict__.update(kwargs)

    async def start(self):
        pass

    async def get_special_commands(self) -> List["Command_Class"]:
        return list()

    async def special_match(self, cmd: str) -> Optional[Tuple["Command", "Match"]]:
        for c in await self.get_special_commands():
            if (match := await c.match(self.owner, cmd)):
                return c, match

    async def parse(self, cmd: str):
        if not (c := await self.special_match(cmd)):
            c = await self.normal_match(cmd)

        if c:
            await self.found_match(cmd, c[0], c[1])
        else:
            await self.no_match(cmd)

    async def no_match(self, cmd: str):
        await self.owner.msg(line=f"No command for: {cmd if len(cmd) < 20 else cmd[0:20] + '...'}. Type 'help' for help!")

    async def normal_match(self, cmd: str) -> Optional[Tuple["Command", "Match"]]:
        for c in await self.get_commands():
            if (match := await c.match(self.owner, cmd)):
                return c, match

    async def found_match(self, cmd, command_class, match):
        command = command_class(self.owner, cmd, match)
        try:
            await command.execute()
        except ValueError as err:
            await self.owner.msg(text=str(err), system_msg=True)

    async def cleanup(self):
        pass

    async def get_commands(self) -> List["Command_Class"]:
        return snekmud.COMMANDS.get(self.category, list())

    async def update(self):
        """
        This is called every tick.
        Presumably used to process pending commands.
        """


class BaseConnectionCommandHandler(BaseCommandHandler):
    pass


class LoginHandler(BaseConnectionCommandHandler):
    category = "connection_login"


class AccountHandler(BaseConnectionCommandHandler):
    category = "connection_account"


class SessionHandler(BaseConnectionCommandHandler):
    category = "connection_session"


class BasePlaySessionCommandHandler(BaseCommandHandler):
    pass


class PlayHandler(BasePlaySessionCommandHandler):
    category = "playhandler_play"


class BaseMobileCommandHandler(BaseCommandHandler):
    pass


class MobileHandler(BaseMobileCommandHandler):
    category = "mobile_mobile"