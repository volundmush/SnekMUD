import orjson
import os
import glob
import pathlib
import re
from typing import List, Optional, Dict, Union
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum
from mudforge.forge.game import GameService as OldGame
from mudforge.utils import generate_name, partial_match


class AccountManager:
    re_name = re.compile(r"(?s)^(\w|\.|-| |'|_)+$")
    re_email = re.compile(r"(?s)^(\w|\.|-| |'|@|_)+$")

    def __init__(self, service):
        self.service = service
        self.accounts: Dict[str, "Account"] = dict()
        self.dir = os.path.join(os.getcwd(), "accounts")
        pathlib.Path(self.dir).mkdir(exist_ok=True)

    def create(self, name: Text, password: str) -> "Account":
        if not self.re_name.match(name.plain):
            raise ValueError("Account names must be simple.")
        if not password:
            raise ValueError("Must include a password.")
        if self.find(name, exact=True):
            raise ValueError("That account already exists!")
        acc_id = generate_name("acc", self.accounts.keys(), gen_length=8)
        acc = self.service.classes["account"]()
        acc.account_id = acc_id
        acc.name = name
        if len(self.accounts) == 0:
            acc.supervisor_level = 1000
        self.accounts[acc_id] = acc

    def find(self, name: Text, exact=False) -> Optional["Account"]:
        if not exact:
            return partial_match(name.plain, self.accounts.values())
        n = name.plain.upper()
        for v in self.accounts.values():
            if v.name.plain.upper() == n:
                return v

    def delete(self, account: Union[str, "Account"]):
        if not hasattr(account, "account_id"):
            if not isinstance(account, str):
                raise ValueError("Account Deletion requires either an Account or its ID.")
            account = self.accounts.get(account, None)
            if not account:
                raise ValueError("Account by ID not found.")
        account.delete()
        file_name = os.path.join(self.dir, f"{account.account_id}.json")
        os.remove(file_name)

    def load(self):
        p = pathlib.Path(self.dir)
        search = p.glob("*.json")
        for j in search:
            with j.open(mode="rb") as f:
                data = orjson.loads(f.read())
                if "account_id" not in data:
                    continue
                acc = self.service.classes["account"]()
                acc.load(data)
                self.accounts[acc.account_id] = acc


class CharacterManager:

    def __init__(self, service):
        self.service = service
        self.characters: Dict[str, "Character"] = dict()


class GameService(OldGame):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accounts = AccountManager(self)