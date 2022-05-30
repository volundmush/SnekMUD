from typing import List, Optional, Dict
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum


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
            case ExitDir.NORTH:
                return ExitDir.SOUTH
            case ExitDir.EAST:
                return ExitDir.WEST
            case ExitDir.SOUTH:
                return ExitDir.NORTH
            case ExitDir.WEST:
                return ExitDir.EAST
            case ExitDir.UP:
                return ExitDir.DOWN
            case ExitDir.DOWN:
                return ExitDir.UP
            case ExitDir.NORTHWEST:
                return ExitDir.SOUTHEAST
            case ExitDir.NORTHEAST:
                return ExitDir.SOUTHWEST
            case ExitDir.SOUTHEAST:
                return ExitDir.NORTHWEST
            case ExitDir.SOUTHWEST:
                return ExitDir.NORTHEAST
            case ExitDir.INWARDS:
                return ExitDir.OUTWARDS
            case ExitDir.OUTWARDS:
                return ExitDir.INWARDS
            case _:
                return ExitDir.UNKNOWN

    def abbr(self) -> str:
        match self:
            case ExitDir.NORTH:
                return "N"
            case ExitDir.EAST:
                return "W"
            case ExitDir.SOUTH:
                return "S"
            case ExitDir.WEST:
                return "W"
            case ExitDir.UP:
                return "U"
            case ExitDir.DOWN:
                return "D"
            case ExitDir.NORTHWEST:
                return "NW"
            case ExitDir.NORTHEAST:
                return "NE"
            case ExitDir.SOUTHEAST:
                return "SE"
            case ExitDir.SOUTHWEST:
                return "SW"
            case ExitDir.INWARDS:
                return "I"
            case ExitDir.OUTWARDS:
                return "O"
            case _:
                return "--"


class ExitFlag(IntFlag):
    pass


class Exit:

    def __init__(self):
        self.description: Optional[Text] = None
        self.keyword: Optional[str] = None
        self.direction: ExitDir = ExitDir.UNKNOWN
        self.flags: int = 0
        self.key: Optional[int] = None
        self.destination: Optional[ref["Room"]] = None
        self.location: Optional[ref["Room"]] = None


class RoomFlag(IntFlag):
    pass


class SectorType(IntEnum):
    UNKNOWN = -1


class Room:

    def __init__(self):
        self.vnum = -1
        self.zone: ref["Zone"] = None
        self.sector_type: SectorType = SectorType.UNKNOWN
        self.name = Text("New Room")
        self.description = Text("No description yet.")
        self.flags: int = 0
        self.exits: Dict[ExitDir, Exit] = dict()
        self.things: WeakSet["Thing"] = WeakSet()
        self.mobiles: WeakSet["Mobile"] = WeakSet()
        self.entrances: WeakValueDictionary[ExitDir, ref["Exit"]] = WeakValueDictionary()