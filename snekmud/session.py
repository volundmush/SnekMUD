import time
import snekmud
from typing import List, Optional, Dict, Any, Union
from weakref import WeakValueDictionary, ref, WeakSet, proxy
from rich.text import Text
from enum import IntFlag, IntEnum
from snekmud.commands.base import HasCommandHandler
from snekmud.utils.comms import ActType, act


class Session(HasCommandHandler):

    def __init__(self, account: "AccountDriver", character: "CharacterInstanceDriver"):
        self.connections: Optional[WeakValueDictionary[str, ref["Connection"]]] = WeakValueDictionary()
        self.account: proxy["AccountDriver"] = proxy(account)
        self.character: proxy["CharacterInstanceDriver"] = proxy(character)
        self.puppet: proxy["CharacterInstanceDriver"] = proxy(character)
        self.created = time.time()
        self.last_user_input = time.time()
        self.cmd_handler: Optional["BaseCommandHandler"] = None
        self.started = False
        character.session = proxy(self)

    async def on_init(self):
        await self.set_cmd_handler(snekmud.COMMAND_HANDLERS["session_character"])

    async def add_connection(self, conn: "Connection"):
        conn.session = self
        self.connections[conn.details.client_id] = conn
        await conn.set_cmd_handler(snekmud.COMMAND_HANDLERS["connection_session"])
        if not self.started:
            self.started = True
            await self.on_first_connect(conn)
        await self.on_add_connection(conn)

    async def prepare_character(self):
        await self.puppet.set_cmd_handler(snekmud.COMMAND_HANDLERS["character_action"])
        location, err = await self.puppet.get_login_room()
        if location:
            await self.puppet.do_move(destination=location)
            await act("$n has entered the game.", actor=self.puppet, act_type=ActType.TO_ROOM)
        if err:
            await self.puppet.msg(line=err, system_msg=True)

    async def on_first_connect(self, conn: "Connection"):
        await self.prepare_character()

    async def on_add_connection(self, conn: "Connection"):
        if self.puppet.location:
            rendered = await self.puppet.render_room(self.puppet.location)
            await self.puppet.msg(line=rendered, system_msg=True)
        else:
            await self.puppet.msg(line="You drift in the void...", system_msg=True)

    def session_id(self):
        return self.character.character.character_id

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
        out["self"] = self.puppet
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