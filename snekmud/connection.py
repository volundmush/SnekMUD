import time
from typing import List, Optional, Union, Any
from rich.text import Text
from mudforge.forge.link import Connection as OldConn

import snekmud
from snekmud.commands.base import HasCommandHandler


class Connection(OldConn, HasCommandHandler):

    def __init__(self, details):
        super().__init__(details)
        self.user: Optional["Account"] = None
        self.cmd_handler: Optional["BaseCommandHandler"] = None
        self.created = time.time()
        self.last_user_input = time.time()

    def get_idle_time(self):
        return self.last_user_input - self.created

    async def msg(self, line: Optional[Union[str, Text]]=None, text: Optional[Union[str, Text]]=None, source=None,
                  relayed_by: Optional[List[Any]]=None, system_msg: bool=True, channel=None):
        if line:
            await self.send_line(line)
        if text:
            await self.send_text(text)

    async def on_start(self):
        """
        Set the initial command handler.
        """
        handler = snekmud.COMMAND_HANDLERS["connection_login"]
        await self.set_cmd_handler(handler)

    async def check_login(self, name: Union[str, Text], password: Union[str, Text]):
        if not (found := snekmud.GAME.accounts.find(name=name, exact=True)):
            raise ValueError(f"Account '{name}' not found.")
        if not found.verify(password):
            raise ValueError("Invalid password.")
        print(f"Located account: {found}")
        await self.process_login(found)

    async def process_login(self, account: "Account"):
        self.user = account
        account.connections[self.details.client_id] = self
        await self.set_cmd_handler(snekmud.COMMAND_HANDLERS["connection_account"])
        print(f"{self} is now using cmd_handler: {self.cmd_handler}")

    async def process_input_text(self, data: str):
        if data == "IDLE":
            return
        await self.cmd_handler.parse(data)
        self.last_user_input = time.time()