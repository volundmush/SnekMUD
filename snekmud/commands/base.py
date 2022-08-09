from typing import List, Optional
import snekmud
import mudforge
from snekmud import exceptions as ex

class MetaCommand(type):
    def __repr__(cls):
        return f"<{cls.__name__}: {cls.name}>"

class Command(metaclass=MetaCommand):
    name = None  # Name must be set to a string!
    aliases = []
    help_category = None
    priority = 0
    min_text = None
    main_category = None
    sub_categories = []
    ex = ex.CommandError

    @classmethod
    async def access(cls, **kwargs) -> bool:
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
        It should return markdown text to display.
        """
        pass

    @classmethod
    async def match(cls, handler, match_obj, partial: bool = False, **kwargs):
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
            return cls(handler, match_obj, **kwargs)
        for x in cls.aliases:
            if clower == x.lower():
                return cls(handler, match_obj, **kwargs)
        if partial and cls.min_text:
            if nlower.startswith(clower) and clower.startswith(cls.min_text.lower()):
                return cls(handler, match_obj, **kwargs)
        return None

    def __init__(self, handler, match_obj, **kwargs):
        """
        Instantiates the command.
        """
        self.handler = handler
        self.match_obj = match_obj
        self.kwargs = kwargs
        self.__dict__.update(kwargs)
        self.__dict__.update(match_obj.groupdict())
        self.parse()

    def parse(self):
        pass

    async def at_pre_execute(self):
        return True

    async def execute(self):
        pass

    async def at_post_execute(self):
        pass

    def send(self, **kwargs):
        self.handler.send(**kwargs)


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

    async def do_match(self, cmd_match, find_func: str, partial: bool, **kwargs) -> Optional["Command"]:
        for c in await getattr(self, find_func)():
            if await c.access(**kwargs) and (cmd := await c.match(self, cmd_match, partial=partial, **kwargs)):
                return cmd

    async def special_match(self, cmd_match, **kwargs) -> Optional["Command"]:
        return await self.do_match(cmd_match, "get_special_commands", self.partial_special, **kwargs)

    async def normal_match(self, cmd_match, **kwargs) -> Optional["Command"]:
        return await self.do_match(cmd_match, "get_commands", self.partial_normal, **kwargs)

    async def reg_match(self, cmd: str):
        return mudforge.CONFIG.CMD_MATCH.match(cmd)

    async def find_cmd(self, cmd_match):
        kwargs = await self.generate_kwargs()
        if not (c := await self.special_match(cmd_match, **kwargs)):
            c = await self.normal_match(cmd_match, **kwargs)
        return c

    async def parse(self, cmd: str):
        if (cmd_match := await self.reg_match(cmd)):
            if (c := await self.find_cmd(cmd_match)):
                await self.found_match(c)
                return
        await self.no_match(cmd)

    async def no_match(self, cmd: str):
        self.send(line=f"No command for: {cmd if len(cmd) < 20 else cmd[0:20] + '...'}. Type 'help' for help!")

    async def found_match(self, cmd):
        try:
            if await cmd.at_pre_execute():
                await cmd.execute()
                await cmd.at_post_execute()
        except ex.CommandError as err:
            self.send(line=str(err))
        except ex.DatabaseError as err:
            self.send(line=str(err))

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

    def send(self, **kwargs):
        self.owner.send(**kwargs)


class ConnectionCommandHandler(BaseCommandHandler):
    main_category = "connection"

    async def generate_kwargs(self):
        out = {"connection": self.owner}
        if self.owner.account:
            out["account"] = self.owner.account
        return out


class GameSessionCommandHandler(BaseCommandHandler):
    main_category = "session"

    async def get_user(self):
        return self.owner.owner

    async def generate_kwargs(self):
        return {"session": self.owner.owner,
                "character": self.owner.character,
                "entity": self.owner.puppet}


class EntityCommandHandler(BaseCommandHandler):
    main_category = "entity"

    async def generate_kwargs(self):
        out = {"entity": self.owner.entity}
        if (sess := snekmud.WORLD.try_component(self.owner.entity, snekmud.COMPONENTS["HasSession"])):
            if sess.session:
                out.update({"session": sess.session, "account": sess.session.account})
        return out
