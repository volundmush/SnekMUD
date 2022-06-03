import time
import snekmud
from typing import List, Optional, Dict, Any, Union
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum
from snekmud.commands.base import HasCommandHandler

class Session(HasCommandHandler):

    def __init__(self, account: "AccountDriver", character: "MobileInstanceDriver"):
        self.connections: Optional[WeakValueDictionary[str, ref["Connection"]]] = WeakValueDictionary()
        self.account: ref["AccountDriver"] = weakref.ref(account)
        self.character: ref["MobileInstanceDriver"] = weakref.ref(character)
        self.puppet: ref["MobileInstanceDriver"] = weakref.ref(character)
        self.created = time.time()
        self.last_user_input = time.time()
        self.cmd_handler: Optional["BaseCommandHandler"] = None
        self.started = False

    async def on_init(self):
        self.set_cmd_handler(snekmud.COMMAND_HANDLERS["session_mobile"])

    async def add_connection(self, conn: "Connection"):
        conn.session = self
        self.connections[conn.details.client_id] = conn
        conn.set_cmd_handler(snekmud.COMMAND_HANDLERS["connection_session"])
        if self.started:
            self.started = True
            await self.on_first_connect(conn)
        await self.on_add_connection(conn)

    async def prepare_character(self):
        pass

    async def on_first_connect(self, conn: "Connection"):
        await self.prepare_character()

    async def on_add_connection(self, conn: "Connection"):
        pass

    def session_id(self):
        return self.character.mobile.character_id

    def __str__(self):
        return self.session_id()

    async def process_command_entry(self, cmd):
        if not self.cmd_handler:
            return
        cmd.session = self
        self.last_user_input = time.time()
        await self.cmd_handler.parse(cmd)

    def get_py_vars(self) -> dict:
        out = {}
        out["character"] = self.character
        out["puppet"] = self.puppet
        return out

    def get_idle_time(self):
        return self.last_user_input - self.created

    def get_conn_time(self):
        return time.time() - self.created

    async def msg(self, line: Optional[Union[str, Text]]=None, text: Optional[Union[str, Text]]=None,
                  source: Optional[Any]=None, relayed_by: Optional[List[Any]]=None, system_msg: bool=True,
                  channel=None, gmcp=None, highlighter: str = "null", **kwargs):
        if not line and not text and not gmcp:
            return
        if relayed_by:
            relayed_by.append(self)
        else:
            relayed_by = [self, ]
        for k, v in self.connections.items():
            await v.msg(line=line, text=text, source=source, relayed_by=relayed_by, system_msg=system_msg,
                        channel=channel, gmcp=gmcp, highlighter=highlighter, **kwargs)

    async def update(self, tick: int):
        """
        Called every tick.
        """

    async def request_logout(self, force: bool = False):
        pass