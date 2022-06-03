from typing import List, Set, Dict
from collections import defaultdict
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
    args: Dict[int, int] = field(default_factory=lambda: defaultdict(0))
    line: int = -1
    sargs: Dict[int, str] = field(default_factory=lambda: defaultdict(0))


class ZoneFlag(IntFlag):
    pass


@dataclass_json
@dataclass(slots=True)
class Zone:
    vnum: int = -1
    name: Text = field(default=Text("New Zone"), metadata=config(encoder=lambda x: x.serialize(), decoder=Text.deserialize))
    lifespan: int = 30
    bottom_vnum: int = -1
    top_vnum: int = -1
    reset_commands: List[ResetCommand] = field(default_factory=list)
    flags: Set[ZoneFlag] = field(default_factory=set)
    builders: List[str] = field(default_factory=list)


class ZoneDriver:

    __slots__ = ["data", "rooms", "mobiles", "things", "scripts", "shops", "guilds", "__weakref__", "age"]

    def __init__(self, zone):
        self.data = zone
        self.age: int = -1
        self.rooms: WeakValueDictionary[int, ref["Room"]] = WeakValueDictionary()
        self.mobiles: WeakValueDictionary[int, ref["Mobile"]] = WeakValueDictionary()
        self.things: WeakValueDictionary[int, ref["Thing"]] = WeakValueDictionary()
        self.scripts: WeakValueDictionary[int, ref["Script"]] = WeakValueDictionary()
        self.shops: WeakValueDictionary[int, ref["Shop"]] = WeakValueDictionary()
        self.guilds: WeakValueDictionary[int, ref["Guild"]] = WeakValueDictionary()

    def __str__(self):
        return str(self.zone.name)