import orjson
import os
import glob
import pathlib
import re
import logging
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

    async def create(self, name: Union[Text, str], password: str, source: str=None) -> "Account":
        if not self.re_name.match(name):
            raise ValueError("Account names must be simple.")
        if not password:
            raise ValueError("Must include a password.")
        if await self.find(name, exact=True):
            raise ValueError("That account already exists!")
        acc_id = generate_name("acc", snekmud.ACCOUNTS.keys(), gen_length=8)
        acc_driver = snekmud.CLASSES["account_driver"]
        if isinstance(name, str):
            name = Text(name)
        acc = acc_driver(snekmud.CLASSES["account"](account_id=acc_id, name=name))
        await acc.set_password(password=password)
        if not len(snekmud.ACCOUNTS):
            logging.info(f"Granting Account {name.plain} root supervisor privileges.")
            acc.account.supervisor_level = 1000
        snekmud.ACCOUNTS[acc_id] = acc

    async def find(self, name: Union[Text, str], exact=False) -> Optional["Account"]:
        name = str(name)
        if not exact:
            return partial_match(name, snekmud.ACCOUNTS.values())
        n = name.upper()
        for v in snekmud.ACCOUNTS.values():
            if str(v).upper() == n:
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
        acc_driver = snekmud.CLASSES["account_driver"]
        search = p.glob("*.json")
        counter = 0
        for j in search:
            with j.open(mode="rb") as f:
                data = orjson.loads(f.read())
                if "account_id" not in data:
                    continue
                acc = acc_driver(acc_class.from_dict(data))
                snekmud.ACCOUNTS[acc.account.account_id] = acc
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
                f.write(orjson.dumps(v.account.to_dict()))
                f.flush()
            counter += 1
        return counter


class CharacterManager:
    re_name = re.compile(r"(?s)^(\w|\.|-| |'|_)+$")

    def __init__(self, service):
        self.service = service
        self.dir = os.path.join(os.getcwd(), "characters")
        pathlib.Path(self.dir).mkdir(exist_ok=True)

    async def create(self, name: Union[str, Text], account: "Account") -> "MobileInstanceDriver":
        if not self.re_name.match(name.plain):
            raise ValueError("Character names must be simple.")
        if not account:
            raise ValueError("Must include an Account.")
        if await self.find(name, exact=True):
            raise ValueError("That character already exists!")
        if isinstance(name, str):
            name = Text(name)
        char_id = generate_name("char", snekmud.CHARACTERS.keys(), gen_length=8)
        char = snekmud.CLASSES["mobile"](account_id=account.account_id, name=name)
        character = snekmud.CLASSES["mobile_instance_driver"](char, char_id)
        snekmud.CHARACTERS[char_id] = character
        return character

    async def find(self, name: Union[str, Text], exact=False) -> Optional["MobileInstanceDriver"]:
        name = str(name)
        if not exact:
            return partial_match(name, snekmud.CHARACTERS.values())
        n = name.upper()
        for v in snekmud.CHARACTERS.values():
            if str(v).upper() == n:
                return v

    async def delete(self, character: Union[str, "Character"]):
        if not hasattr(character, "character_id"):
            if not isinstance(character, str):
                raise ValueError("Account Deletion requires either an Account or its ID.")
            character = snekmud.CHARACTERS.get(character, None)
            if not character:
                raise ValueError("Character by ID not found.")
        character.delete()
        file_name = os.path.join(self.dir, f"{character.character_id}.json")
        os.remove(file_name)

    async def load(self) -> int:
        p = pathlib.Path(self.dir)
        char_class = snekmud.CLASSES["mobile"]
        char_driver = snekmud.CLASSES["mobile_instance_driver"]
        search = p.glob("*.json")
        counter = 0
        for j in search:
            with j.open(mode="rb") as f:
                data = orjson.loads(f.read())
                if "character_id" not in data:
                    continue
                char = char_class.from_dict(data)
                character = char_driver(char, char.character_id)
                snekmud.CHARACTERS[char.character_id] = character
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

    async def create_or_join_session(self, cmd: "CommandEntry", character: "MobileInstanceDriver"):
        if not (char_id := character.mobile.character_id):
            raise ValueError("That is not a player character!")
        if not (session := snekmud.SESSIONS.get(char_id, None)):
            session = snekmud.CLASSES["session"](cmd.connection.user, character)
            snekmud.SESSIONS[char_id] = session
            await session.on_init()
        await session.add_connection(cmd.connection)