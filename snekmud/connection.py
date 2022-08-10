from mudforge.net.game_conn import GameConnection as OldConn
import snekmud
from snekmud.db.accounts.models import Account
from snekmud.db.gamesessions.models import GameSession
from snekmud.db.players.models import PlayerCharacter
from snekmud.exceptions import CommandError
import time
from mudrich.evennia import EvenniaToRich
from rich.text import Text


class GameConnection(OldConn):
    rich_kwargs = ["text", "line", "prompt"]

    def export_copyover(self) -> dict:
        out = super().export_copyover()
        if self.account:
            out["account"] = self.account.id
        if self.session:
            out["session"] = self.session.id.id
        out["cmdhandler"] = self.cmdhandler_name
        out["time_last_activity"] = time.time()
        return out

    @classmethod
    async def from_copyover(cls, conn, data):
        out = cls(conn)
        if (last := data.pop("time_last_activity", None)):
            out.time_last_activity = last
        if (acc_id := data.pop("account", None)) is not None:
            out.account = Account.objects.get(id=acc_id)
        if (cmd_name := data.pop("cmdhandler", None)):
            await out.set_cmdhandler(cmd_name)
        if (sess_id := data.pop("session")):
            sess = GameSession.objects.get(id=sess_id)
            await sess.handler.add_connection(out)
        return out

    def __init__(self, conn):
        super().__init__(conn)
        self.account = None
        self.cmdhandler = None
        self.cmdhandler_name = None
        self.session = None
        self.time_last_activity = time.time()

    def write(self, b: str):
        """
        Gives this class the interface of IO Writing.
        """
        if not b.isspace():
            self.conn.send_python(b.rstrip("\n"))

    def flush(self):
        """
        Do not remove. Dummy method related to IO writing interface.
        """

    async def start(self, copyover=False):
        if not copyover:
            if (text := snekmud.STATIC_TEXT.get("greet", None)):
                self.send_line(text)
            await self.set_cmdhandler("Login")

    async def set_cmdhandler(self, cmdhandler: str, **kwargs):
        if not (p := snekmud.CMDHANDLERS["Connection"].get(cmdhandler, None)):
            self.send(line=f"ERROR: CmdHandler {cmdhandler} not found for Connections, contact staff")
            return
        if self.cmdhandler:
            await self.cmdhandler.close()
        self.cmdhandler = p(self, **kwargs)
        self.cmdhandler_name = cmdhandler
        await self.cmdhandler.start()

    async def process_input_text(self, data: str):
        if data == "IDLE":
            return
        self.time_last_activity = time.time()
        if self.cmdhandler:
            await self.cmdhandler.parse(data)

    async def check_login(self, name: str, password: str):
        if (found := Account.objects.filter(username__iexact=name).first()):
            if found.check_password(password):
                await self.login_as(found)
                return
        raise CommandError("Invalid username or password.")

    async def login_as(self, account):
        self.account = account
        await self.set_cmdhandler("Account")

    def send(self, **kwargs):
        for kw in self.rich_kwargs:
            if (kw_text := kwargs.pop(kw, None)) is not None:
                if not hasattr(kw_text, "__rich_console__"):
                    if not isinstance(kw_text, str):
                        kw_text = str(kw_text)
                    kw_text = EvenniaToRich(kw_text)
                getattr(self, f"send_{kw}")(kw_text)
        if (py := kwargs.pop("python", None)) is not None:
            if not hasattr(py, "__rich_console__"):
                if not isinstance(py, str):
                    py = repr(py)
            self.send_python(py)

    def time_connected(self):
        return time.time() - self.details.connected

    def time_idle(self):
        return time.time() - self.time_last_activity

    async def at_bind_gamesession(self):
        await self.set_cmdhandler("Session")

    async def at_unbind_gamesession(self, sess):
        await self.set_cmdhandler("Account")

    async def can_join_session(self, game_session):
        return True

    async def can_create_session(self, player_character):
        return True

    async def create_or_join_gamesession(self, character_id: int):
        async def do_bind(sess):
            await sess.handler.add_connection(self)
            await self.at_bind_gamesession()

        if not (player := PlayerCharacter.objects.filter(id=character_id).first()):
            raise CommandError(f"Player ID {character_id} not found.")
        if (gsess := GameSession.objects.filter(id=player).first()):
            if gsess.account != self.account:
                raise CommandError(f"This character is being used by a different account!")
            if await self.can_join_session(gsess):
                await do_bind(gsess)
                await gsess.handler.on_additional_connection(self)
            else:
                raise CommandError(f"Cannot join game session as {player.name}")
        else:
            if await self.can_create_session(player):
                pass
            else:
                raise CommandError(f"Cannot create game session for {player.name}")
            sess = self.account.sessions.create(id=player)
            await do_bind(sess)
            await sess.handler.on_first_connection(self)