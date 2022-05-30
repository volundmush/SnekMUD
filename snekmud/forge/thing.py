from typing import List, Optional, Dict
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum


class WearFlag(IntFlag):
    pass


class ExtraFlag(IntFlag):
    pass


class ThingFlag(IntFlag):
    pass


class ThingType(IntEnum):
    JUNK = -1


class Thing:

    __slots__ = ["vnum", "type", "level", "wear_flags", "extra_flags", "flags", "cost", "rent_per_day",
                 "timer", "name", "description", "short_desc", "action_desc", "carried_by", "worn_by",
                 "wear_loc", "inside", "contents", "__weakref__"]

    def __init__(self):
        self.vnum: int = -1
        self.type: ThingType = ThingType.JUNK
        self.level: int = -1
        self.wear_flags: int = 0
        self.extra_flags: int = 0
        self.flags: int = 0
        self.cost: int = 0
        self.rent_per_day: int = 0
        self.timer: int = 0
        self.name: Text = Text("New Thing")
        self.description: Optional[Text] = None
        self.short_desc: Optional[Text] = None
        self.action_desc: Optional[Text] = None

        self.carried_by: Optional[ref["Mobile"]] = None
        self.worn_by: Optional[ref["Mobile"]] = None
        self.wear_loc: Optional[int] = None

        self.inside: Optional[ref["Mobile"]] = None
        self.contents: WeakSet[ref["Thing"]] = WeakSet()

