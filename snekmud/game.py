import orjson
import os
import glob
import pathlib
import re
from typing import List, Optional, Dict, Union, Set
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum
from mudforge.forge.game import GameService as OldGame
from mudforge.utils import generate_name, partial_match, import_from_module

import snekmud


class AccountManager:
    re_name = re.compile(r"(?s)^(\w|\.|-| |'|_)+$")
    re_email = re.compile(r"(?s)^(\w|\.|-| |'|@|_)+$")

    def __init__(self, service):
        self.service = service
        self.dir = os.path.join(os.getcwd(), "accounts")
        pathlib.Path(self.dir).mkdir(exist_ok=True)

    async def create(self, name: str, password: str, source: str=None) -> "Account":
        if not self.re_name.match(name):
            raise ValueError("Account names must be simple.")
        if not password:
            raise ValueError("Must include a password.")
        if await self.find(name, exact=True):
            raise ValueError("That account already exists!")
        acc_id = generate_name("acc", snekmud.ACCOUNTS.keys(), gen_length=8)
        acc = snekmud.CLASSES["account"]()
        acc.account_id = acc_id
        acc.name = name
        if len(snekmud.ACCOUNTS) == 0:
            acc.supervisor_level = 1000
        snekmud.ACCOUNTS[acc_id] = acc

    async def find(self, name: str, exact=False) -> Optional["Account"]:
        if not exact:
            return partial_match(name, snekmud.ACCOUNTS.values())
        n = name.upper()
        for v in snekmud.ACCOUNTS.values():
            if v.name.upper() == n:
                return v

    async def delete(self, account: Union[str, "Account"]):
        if not hasattr(account, "account_id"):
            if not isinstance(account, str):
                raise ValueError("Account Deletion requires either an Account or its ID.")
            account = snekmud.ACCOUNTS.get(account, None)
            if not account:
                raise ValueError("Account by ID not found.")
        account.delete()
        file_name = os.path.join(self.dir, f"{account.account_id}.json")
        os.remove(file_name)

    async def load(self) -> int:
        p = pathlib.Path(self.dir)
        acc_class = snekmud.CLASSES["account"]
        search = p.glob("*.json")
        counter = 0
        for j in search:
            with j.open(mode="rb") as f:
                data = orjson.loads(f.read())
                if "account_id" not in data:
                    continue
                acc = acc_class()
                acc.load(data)
                snekmud.ACCOUNTS[acc.account_id] = acc
                counter += 1
        return counter

    async def save_all(self) -> int:
        p = pathlib.Path(self.dir)
        counter = 0
        for k, v in snekmud.ACCOUNTS.items():
            if not v:
                continue
            if not v.dirty:
                continue
            fp = p.joinpath(f"{k}.json")
            with fp.open(mode="wb") as f:
                f.write(orjson.dumps(v.export()))
                f.flush()
            counter += 1
        return counter


class CharacterManager:
    re_name = re.compile(r"(?s)^(\w|\.|-| |'|_)+$")

    def __init__(self, service):
        self.service = service
        self.dir = os.path.join(os.getcwd(), "characters")
        pathlib.Path(self.dir).mkdir(exist_ok=True)

    async def create(self, name: Text, account: "Account") -> "Character":
        if not self.re_name.match(name.plain):
            raise ValueError("Character names must be simple.")
        if not account:
            raise ValueError("Must include an Account.")
        if await self.find(name, exact=True):
            raise ValueError("That character already exists!")
        char_id = generate_name("char", snekmud.CHARACTERS.keys(), gen_length=8)
        char = snekmud.CLASSES["character"]()
        char.account_id = char_id
        char.name = name
        if len(snekmud.CHARACTERS) == 0:
            char.supervisor_level = 1000
        snekmud.CHARACTERS[char_id] = char

    async def find(self, name: Union[str, Text], exact=False) -> Optional["Character"]:
        if not exact:
            return partial_match(str(name), snekmud.CHARACTERS.values())
        n = str(name).upper()
        for v in snekmud.CHARACTERS.values():
            if str(v.name).upper() == n:
                return v

    async def delete(self, character: Union[str, "Character"]):
        if not hasattr(character, "character_id"):
            if not isinstance(character, str):
                raise ValueError("Account Deletion requires either an Account or its ID.")
            character = snekmud.CHARACTERS.get(character, None)
            if not character:
                raise ValueError("Account by ID not found.")
        character.delete()
        file_name = os.path.join(self.dir, f"{character.character_id}.json")
        os.remove(file_name)

    async def load(self) -> int:
        p = pathlib.Path(self.dir)
        char_class = snekmud.CLASSES["character"]
        search = p.glob("*.json")
        counter = 0
        for j in search:
            with j.open(mode="rb") as f:
                data = orjson.loads(f.read())
                if "character_id" not in data:
                    continue
                character = char_class()
                character.load(data)
                snekmud.CHARACTERS[character.character_id] = character
                counter += 1
        return counter

    async def save_all(self) -> int:
        p = pathlib.Path(self.dir)
        counter = 0
        for k, v in snekmud.CHARACTERS.items():
            if not v:
                continue
            if not v.dirty:
                continue
            fp = p.joinpath(f"{k}.json")
            with fp.open(mode="wb") as f:
                f.write(orjson.dumps(v.export()))
                f.flush()
            counter += 1
        return counter


class GameService(OldGame):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accounts = AccountManager(self)
        self.characters = CharacterManager(self)

    async def prepare_characters(self) -> Set[str]:
        no_match = set()
        for k, v in snekmud.CHARACTERS.items():
            if not (acc := snekmud.ACCOUNTS.get(v.account_id, None)):
                no_match.add(k)
                continue
            acc.characters[k] = v
        for k in no_match:
            snekmud.CHARACTERS.pop(k, None)
        return no_match