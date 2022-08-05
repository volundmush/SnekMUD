from mudforge.net.game_conn import GameConnection as OldConn
from snekmud.parsers.conn_login import LoginParser
from snekmud.parsers.conn_account import AccountMenu
import snekmud


class GameConnection(OldConn):

    def __init__(self, conn):
        super().__init__(conn)

        self.account = None
        self.cmdhandler = None
        self.session = None

    async def start(self):
        await self.on_start()

    async def on_start(self):
        await self.set_cmdhandler("Login")

    async def set_cmdhandler(self, cmdhandler: str, **kwargs):
        if not (p := snekmud.CMDHANDLERS["Connection"].get(cmdhandler, None)):
            self.send_line(f"ERROR: CmdHandler {cmdhandler} not found for Connections, contact staff")
            return
        if self.cmdhandler:
            await self.cmdhandler.close()
        self.cmdhandler = p(self, **kwargs)
        await self.cmdhandler.start()

    async def process_input_text(self, data: str):
        if self.cmdhandler:
            await self.cmdhandler.parse(data)

    async def login_as(self, account):
        self.account = account
        await self.set_cmdhandler("Account")

    def send(self, **kwargs):
        if (text := kwargs.pop("text", None)) is not None:
            self.send_text(text)
        if (line := kwargs.pop("line", None)) is not None:
            self.send_line(line)
