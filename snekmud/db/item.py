from typing import List, Optional, Dict, Set
from collections import defaultdict
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from snekmud.db.entity import EntityInstanceDriver, EntityPrototypeDriver


class ItemPrototypeDriver(EntityPrototypeDriver):
    pass


class ItemInstanceDriver(EntityPrototypeDriver):

    __slots__ = ["carried_by", "worn_by", "wear_loc", "inside", "contents", "location", "timer"]

    def __init__(self, object):
        super().__init__(object)
        self.location: Optional[ref["RoomDriver"]]
        self.carried_by: Optional[ref["CharacterInstanceDriver"]] = None
        self.worn_by: Optional[ref["CharacterInstanceDriver"]] = None
        self.wear_loc: Optional[int] = None
        self.inside: Optional[ref["ObjectDriver"]] = None
        self.contents: WeakSet[ref["ObjectDriver"]] = WeakSet()
        self.timer: int = 0
