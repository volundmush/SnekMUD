from typing import List, Optional, Dict, Set, Union, Tuple
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum
import snekmud
import sys
import re
import time
from rich.traceback import Traceback
from rich.highlighter import ReprHighlighter

class CommandException(Exception):
    pass


class CommandEntry:

    def __init__(self, text: str):
        self.text = text
        self.connection = None
        self.session = None
        self.mobile = None

    def __str__(self):
        return self.text

    def organize(self):
        output = list()
        for c in ("connection", "session", "mobile"):
            if (found := getattr(self, c)):
                output.append(found)
        return output

    def top(self):
        entities = self.organize()
        if entities:
            return entities[0]

    def bottom(self):
        entities = self.organize()
        if entities:
            return entities[-1]

    def get_slevel(self, ignore_spoof=False):
        if self.connection:
            return self.connection.get_slevel(ignore_spoof=ignore_spoof)
        return 0

class Command:
    name = None  # Name must be set to a string!
    aliases = []
    help_category = None

    @classmethod
    async def access(cls, entry: CommandEntry):
        """
        This returns true if <enactor> is able to see and use this command.
        Use this for admin permissions locks as well as conditional access, such as
        'is the enactor currently in a certain kind of location'.
        """
        return True

    @classmethod
    async def help(cls, entry: CommandEntry):
        """
        This is called by the command-help system if help is called on this command.
        """
        pass

    @classmethod
    async def match(cls, entry: CommandEntry):
        """
        Called by the CommandGroup to determine if this command matches.
        Returns False or a Regex Match object.
        Or any kind of match, really. The parsed match will be returned and re-used by .execute()
        so use whatever you want.
        """
        return cls.re_match.fullmatch(entry.text)

    def __init__(self, user: "HasCommandHandler", entry: CommandEntry, match_obj):
        """
        Instantiates the command.
        """
        self.entry = entry
        self.match_obj = match_obj
        self.user: Union["Connection", "Session", "Mobile"] = user

    async def execute(self):
        pass


class PyCommand(Command):
    name = "@py"
    re_match = re.compile(r"^(?P<cmd>@py)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)
    help_category = "System"

    def available_vars(self):
        return {
            "game": snekmud.GAME,
            "snek_api": snekmud
        }

    @classmethod
    async def access(cls, entry):
        return entry.get_slevel() >= 10

    def flush(self):
        pass

    def write(self, text):
        out = fmt.FormatList(self.executor)
        out.add(fmt.PyDebug(text.rsplit("\n", 1)[0]))
        self.executor.send(out)

    async def execute(self):
        mdict = self.match_obj.groupdict()
        args = mdict.get("args", None)
        if not args:
            raise CommandException("@py requires arguments!")
        await self.user.msg(line=Text(f">>> {args}"), system_msg=True)
        duration = ""
        ret = None

        try:
            # reroute standard output to game client console
            old_stdout = sys.stdout
            old_stderr = sys.stderr

            sys.stdout = self
            sys.stderr = self

            try:
                pycode_compiled = compile(args, "", "eval")
            except Exception:
                pycode_compiled = compile(args, "", "exec")

            measure_time = True

            if measure_time:
                t0 = time.time()
                ret = eval(pycode_compiled, {}, self.available_vars())
                t1 = time.time()
                duration = " (runtime ~ %.4f ms)" % ((t1 - t0) * 1000)
            else:
                ret = eval(pycode_compiled, {}, self.available_vars())
        except Exception:
            exc_type, exc_value, tb = sys.exc_info()
            trace = Traceback.extract(exc_type, exc_value, tb, show_locals=False)
            await self.user.msg(line=Traceback(trace), system_msg=True)
        finally:
            # return to old stdout
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        await self.user.msg(line=repr(ret), system_msg=True, highlighter="python")

        if duration:
            await self.user.msg(line=Text(duration), system_msg=True)


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

    async def special_match(self, cmd: CommandEntry) -> Optional[Tuple["Command", "Match"]]:
        for c in await self.get_special_commands():
            if (match := await c.match(cmd)):
                return c, match

    async def parse(self, cmd: CommandEntry):
        if not (c := await self.special_match(cmd)):
            c = await self.normal_match(cmd)
        if c:
            await self.found_match(cmd, c[0], c[1])
        else:
            await self.no_match(cmd)

    async def no_match(self, cmd: CommandEntry):
        await self.owner.msg(line=f"No command for: {cmd.text if len(cmd.text) < 20 else cmd.text[0:20] + '...'}. Type 'help' for help!")

    async def normal_match(self, cmd: CommandEntry) -> Optional[Tuple["Command", "Match"]]:
        for c in await self.get_commands():
            if (match := await c.match(cmd)):
                return c, match

    async def found_match(self, cmd, command_class, match):
        command = command_class(self.owner, cmd, match)
        try:
            await command.execute()
        except ValueError as err:
            await self.owner.msg(text=str(err), system_msg=True)
        except CommandException as err:
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