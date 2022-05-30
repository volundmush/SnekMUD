from passlib.context import CryptContext
from typing import List, Optional, Dict
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum
from mudforge.utils import generate_name
from snekmud.forge.misc import Exportable

CRYPT = CryptContext(schemes=["argon2",])


class Account(Exportable):
    direct_fields = ["account_id", "password_hash", "max_characters", "supervisor_level", "email", "created"]
    rich_fields = ["name"]

    __slots__ = ["account_id", "name", "password_hash", "characters", "max_characters", "supervisor_level",
                 "connections", "email", "created", "__weakref__"]

    def __init__(self):
        self.account_id = ""
        self.name = Text("New Account")
        self.password_hash: Optional[str] = None
        self.characters: WeakValueDictionary[str, ref["Character"]] = WeakValueDictionary()
        self.max_characters: int = 3
        self.supervisor_level = 0
        self.connections: WeakValueDictionary[str, ref["Connection"]] = WeakValueDictionary()
        self.email: Optional[str] = None
        self.created: int = 0

    def __str__(self):
        return self.name.plain

    async def set_password(self, password: str):
        self.password_hash = CRYPT.hash(password)

    async def verify_password(self, password: str):
        return CRYPT.verify(password, self.password_hash)

    def delete(self):
        pass
