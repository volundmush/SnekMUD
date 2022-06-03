import datetime
from passlib.context import CryptContext
from typing import Optional, Union
from weakref import WeakValueDictionary, ref
from rich.text import Text
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config

CRYPT = CryptContext(schemes=["argon2", ])

def _new_account():
    return Text("New Account")

@dataclass_json
@dataclass(slots=True)
class Account:
    account_id: str = ""
    name: Text = field(default_factory=_new_account, metadata=config(encoder=lambda x: x.serialize(), decoder=Text.deserialize))
    password_hash: Optional[str] = None
    max_characters: int = 3
    supervisor_level: int = 0
    email: Optional[str] = None
    created: datetime.datetime


class AccountDriver:

    __slots__ = ["account", "characters", "connections", "dirty", "__weakref__"]

    def __init__(self, account):
        self.account = account
        self.characters: WeakValueDictionary[str, ref["Character"]] = WeakValueDictionary()
        self.connections: WeakValueDictionary[str, ref["Connection"]] = WeakValueDictionary()
        self.dirty = False

    def __str__(self):
        return str(self.account.name)

    async def set_password(self, password: str):
        self.account.password_hash = CRYPT.hash(password)

    async def verify_password(self, password: str):
        return CRYPT.verify(password, self.account.password_hash)

    def delete(self):
        pass
