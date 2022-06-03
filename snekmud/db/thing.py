from typing import List, Optional, Dict
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config

class WearFlag(IntFlag):
    pass


class ExtraFlag(IntFlag):
    pass


class ThingFlag(IntFlag):
    pass


class ThingType(IntEnum):
    JUNK = -1


@dataclass_json
@dataclass(slots=True)
class Thing:
    vnum: int = -1
    thing_type: ThingType = ThingType.JUNK
    level: int = -1
    wear_flags: int = 0
    extra_flags: int = 0
    flags: int = 0
    cost: int = 0
    rent_per_day: int = 0
    timer: int = 0
    name: Text = field(default=Text("New Thing"), metadata=config(encoder=lambda x: x.serialize(), decoder=Text.deserialize))
    description: Text = field(default=Text("New Room"), metadata=config(encoder=lambda x: x.serialize(), decoder=Text.deserialize))
    short_desc: Text = field(default=Text("New Room"), metadata=config(encoder=lambda x: x.serialize(), decoder=Text.deserialize))
    action_desc: Text = field(default=Text("New Room"), metadata=config(encoder=lambda x: x.serialize(), decoder=Text.deserialize))


class ThingDriver:

    __slots__ = ["__weakref__", "thing", "carried_by", "worn_by", "wear_loc", "inside", "contents"]

    def __init__(self, thing):
        self.thing = thing

        self.carried_by: Optional[ref["Mobile"]] = None
        self.worn_by: Optional[ref["Mobile"]] = None
        self.wear_loc: Optional[int] = None

        self.inside: Optional[ref["Mobile"]] = None
        self.contents: WeakSet[ref["Thing"]] = WeakSet()

