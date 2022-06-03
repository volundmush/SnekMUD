from typing import List
from weakref import WeakValueDictionary, ref
from rich.text import Text
from enum import IntFlag
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config

@dataclass_json
@dataclass(slots=True)
class ResetCommand:
    command: str = ""
    if_flag: bool = False
    args: List[int] = field(default_factory=list)
    line: int = -1
    sargs: List[str] = field(default_factory=list)


class ZoneFlag(IntFlag):
    pass

def _new_zone():
    return Text("New Zone")

@dataclass_json
@dataclass(slots=True)
class Zone:
    vnum: int = -1
    name: Text = field(default=Text("New Zone"), metadata=config(encoder=lambda x: x.serialize(), decoder=Text.deserialize))
    lifespan: int = 30
    bottom_vnum: int = -1
    top_vnum: int = -1
    reset_commands: List[ResetCommand] = field(default_factory=list)
    flags: int = 0


class ZoneDriver:

    __slots__ = ["data", "rooms", "mobiles", "things", "triggers", "shops", "guilds", "__weakref__", "age"]

    def __init__(self, zone):
        self.data = zone
        self.age: int = -1
        self.rooms: WeakValueDictionary[int, ref["Room"]] = WeakValueDictionary()
        self.mobiles: WeakValueDictionary[int, ref["Mobile"]] = WeakValueDictionary()
        self.things: WeakValueDictionary[int, ref["Thing"]] = WeakValueDictionary()
        self.triggers: WeakValueDictionary[int, ref["Trigger"]] = WeakValueDictionary()
        self.shops: WeakValueDictionary[int, ref["Shop"]] = WeakValueDictionary()
        self.guilds: WeakValueDictionary[int, ref["Guild"]] = WeakValueDictionary()
