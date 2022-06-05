import datetime
import pickle
from passlib.context import CryptContext
from typing import Optional, Union, Any, List
from weakref import WeakValueDictionary, ref
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config

from rich.text import Text
from rich.layout import Layout
from rich.style import Style
from rich.box import ASCII, ASCII2, ASCII_DOUBLE_HEAD
from rich.table import Table
from rich.panel import Panel

CRYPT = CryptContext(schemes=["argon2", ])

def _new_account():
    return Text("New Account")

@dataclass_json
@dataclass(slots=True)
class Account:
    account_id: str = ""
    name: str = "New Account"
    password_hash: Optional[str] = None
    password: Optional[str] = None
    max_characters: int = 3
    supervisor_level: int = 0
    email: Optional[str] = None
    created: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    last_login: Optional[datetime.datetime] = None
    earned_rpp: int = 0
    current_rpp: int = 0


class AccountDriver:

    __slots__ = ["account", "characters", "connections", "dirty", "__weakref__"]

    def __init__(self, account):
        self.account = account
        self.characters: WeakValueDictionary[str, ref["CharacterInstanceDriver"]] = WeakValueDictionary()
        self.connections: WeakValueDictionary[str, ref["Connection"]] = WeakValueDictionary()
        self.dirty = False

    def __str__(self):
        return str(self.account.name)

    async def set_password(self, password: str):
        self.account.password_hash = CRYPT.hash(password)
        self.account.password = None

    async def verify_password(self, password: str):
        if self.account.password:
            if self.account.password == password:
                await self.set_password(password)
        return CRYPT.verify(password, self.account.password_hash)

    def delete(self):
        pass

    async def update(self, tick: int):
        """
        Called every tick.
        """

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

    async def get_characters(self) -> List["CharacterInstanceDriver"]:
        return [c for c in self.characters.values() if c]

    async def login_screen(self, connection: "Connection"):

        all_table = Table(box=ASCII2, safe_box=True, expand=True, border_style="bold magenta")
        all_table.add_column("Account: " + self.account.name, justify="center")

        # Connections
        conn_table = Table(title="Connections", box=ASCII2, safe_box=True, expand=True, border_style="bold magenta")
        conn_table.add_column("Protocol", overflow="fold")
        conn_table.add_column("Address", overflow="fold")
        conn_table.add_column("Conn_ID", overflow="fold")
        conn_table.add_column("Conn", overflow="fold", max_width=5)
        conn_table.add_column("Idle", overflow="fold", max_width=5)
        for k, v in self.connections.items():
            if not v:
                continue
            conn_table.add_row(str(v.details.protocol), v.details.host_address, v.details.client_id,
                               f"{int(v.get_conn_time())}", f"{int(v.get_idle_time())}")

        # Sessions
        sess_table = Table(title="Characters", box=ASCII2, safe_box=True, expand=True, border_style="bold magenta")
        sess_table.add_column("Name", overflow="fold")
        sess_table.add_column("Connections", overflow="fold")
        sess_table.add_column("Runtime", overflow="fold", max_width=5)
        sess_table.add_column("Idle", overflow="fold", max_width=5)
        for k, v in self.characters.items():
            if not v:
                continue
            if v.session:
                sess_table.add_row(v.entity.name, ", ".join(v.session.connections.keys()),
                                   f"{int(v.get_conn_time())}", f"{int(v.get_idle_time())}")
            else:
                sess_table.add_row(v.entity.name, "N/A", "N/A", "N/A")

        all_table.add_row(conn_table)
        all_table.add_row(sess_table)

        return all_table
