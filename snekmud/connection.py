import time
from typing import List, Optional, Union, Any
from rich.text import Text
from mudforge.forge.link import Connection as OldConn

import snekmud
from snekmud.commands.base import HasCommandHandler, CommandEntry


class Connection(OldConn, HasCommandHandler):

    def __init__(self, details):
        super().__init__(details)
        self.user: Optional["Account"] = None
        self.cmd_handler: Optional["BaseCommandHandler"] = None
        self.created = time.time()
        self.last_user_input = time.time()
        self.session: Optiona["Session"] = None
        self.fake_slevel = 0

    def get_slevel(self, ignore_spoof=False):
        if not self.user:
            return -1
        if ignore_spoof:
            return self.user.account.supervisor_level
        return max(min(self.fake_slevel, self.user.account.supervisor_level),0)

    def get_idle_time(self):
        return self.last_user_input - self.created

    def get_conn_time(self):
        return time.time() - self.created

    async def msg(self, line: Optional[Union[str, Text]]=None, text: Optional[Union[str, Text]]=None, source=None,
                  relayed_by: Optional[List[Any]]=None, system_msg: bool=True, channel=None, gmcp=None,
                  highlighter: str = "null", **kwargs):
        if line:
            await self.send_line(line, highlighter, **kwargs)
        if text:
            await self.send_text(text, highlighter, **kwargs)
        if gmcp:
            await self.send_gmcp(gmcp, highlighter, **kwargs)

    async def on_start(self):
        """
        Set the initial command handler.
        """
        handler = snekmud.COMMAND_HANDLERS["connection_login"]
        await self.set_cmd_handler(handler)

    async def check_login(self, name: Union[str, Text], password: Union[str, Text]):
        if not (found := await snekmud.GAME.accounts.find(name=name, exact=True)):
            raise ValueError(f"Account '{name}' not found.")
        if not await found.verify_password(password):
            raise ValueError("Invalid password.")
        await self.process_login(found)

    async def process_login(self, account: "AccountDriver"):
        self.user = account
        account.connections[self.details.client_id] = self
        login_screen = await account.login_screen(self)
        await self.msg(line=login_screen, system_msg=True)
        await self.set_cmd_handler(snekmud.COMMAND_HANDLERS["connection_account"])

    async def process_input_text(self, data: str):
        if data == "IDLE":
            return
        self.last_user_input = time.time()
        entry = CommandEntry(data)
        entry.connection = self
        await self.cmd_handler.parse(entry)

    async def update(self, tick: int):
        """
        Called every tick.
        """
