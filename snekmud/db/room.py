from typing import List, Optional, Dict
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config


class ExitDir(IntEnum):
    UNKNOWN = -1
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    UP = 4
    DOWN = 5
    NORTHWEST = 6
    NORTHEAST = 7
    SOUTHEAST = 8
    SOUTHWEST = 9
    INWARDS = 10
    OUTWARDS = 11

    def reverse(self) -> "ExitDir":
        match self:
            case ExitDir.NORTH | ExitDir.EAST | ExitDir.NORTHWEST | ExitDir.NORTHEAST:
                return ExitDir(self+2)
            case ExitDir.SOUTH | ExitDir.WEST | ExitDir.SOUTHEAST | ExitDir.SOUTHWEST:
                return ExitDir(self-2)
            case ExitDir.INWARDS:
                return ExitDir.OUTWARDS
            case ExitDir.OUTWARDS:
                return ExitDir.INWARDS
            case _:
                return ExitDir.UNKNOWN

    def abbr(self) -> str:
        match self:
            case ExitDir.NORTH | ExitDir.EAST | ExitDir.SOUTH | ExitDir.WEST | ExitDir.UP | ExitDir.DOWN:
                return self.name.lower()[0]
            case ExitDir.NORTHWEST | ExitDir.NORTHEAST | ExitDir.SOUTHEAST | ExitDir.SOUTHWEST:
                return self.name.lower()[0,5]
            case ExitDir.INWARDS:
                return "in"
            case ExitDir.OUTWARDS:
                return "out"
            case _:
                return "--"


class ExitFlag(IntFlag):
    pass


@dataclass_json
@dataclass(slots=True)
class Exit:

    def __init__(self):
        self.description: Text = field(default=Text(""), metadata=config(encoder=lambda x: x.serialize(), decoder=Text.deserialize))
        self.keyword: Optional[str] = None
        self.direction: ExitDir = ExitDir.UNKNOWN
        self.flags: int = 0
        self.key: Optional[int] = None
        self.destination: Optional[int] = None
        self.location: Optional[int] = None


class ExitDriver:

    __slots__ = ["__weakref__", "destination", "location", "exit"]

    def __init__(self, exit):
        self.exit = exit
        self.destination: Optional[ref["Room"]] = None
        self.location: Optional[ref["Room"]] = None


class RoomFlag(IntFlag):
    pass


class SectorType(IntEnum):
    UNKNOWN = -1
    INSIDE = 0
    CITY = 1
    PLAIN = 2
    FOREST = 3
    HILLS = 4
    MOUNTAINS = 5
    SHALLOWS = 6
    WATER_FLY = 7
    SKY = 8
    UNDERWATER = 9
    SHOP = 10
    IMPORTANT = 11
    DESERT = 12
    SPACE = 13
    LAVA = 14

    def abbr(self) -> str:
        match self:
            case SectorType.SHOP:
                return "$"
            case SectorType.IMPORTANT:
                return "#"
            case _:
                return self.name[0]


@dataclass_json
@dataclass(slots=True)
class Room:
    vnum: int = -1
    zone: int = -1
    name: Text = field(default=Text("New Room"), metadata=config(encoder=lambda x: x.serialize(), decoder=Text.deserialize))
    description: Text = field(default=Text("No description yet."), metadata=config(encoder=lambda x: x.serialize(), decoder=Text.deserialize))
    flags: int = 0
    exits: Dict[ExitDir, Exit] = field(default_factory=dict)


class RoomDriver:

    __slots__ = ["__weakref__", "room", "exits", "things", "mobiles", "entrances"]

    def __init__(self, room):
        self.room = room
        self.exits: Dict[ExitDir, ExitDriver] = dict()
        self.things: WeakSet["Thing"] = WeakSet()
        self.mobiles: WeakSet["Mobile"] = WeakSet()
        self.entrances: WeakValueDictionary[ExitDir, ref["Exit"]] = WeakValueDictionary()