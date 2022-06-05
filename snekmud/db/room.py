from typing import List, Optional, Dict, Set, Union, Tuple
from weakref import WeakValueDictionary, ref, WeakSet, proxy
from rich.text import Text
from enum import IntFlag, IntEnum
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
import snekmud
from snekmud.db.misc import Location
from marshmallow import Schema, fields


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

    def describe_move(self) -> str:
        match self:
            case ExitDir.INWARDS:
                return "outside"
            case ExitDir.OUTWARDS:
                return "inside"
            case ExitDir.UP:
                return "below"
            case ExitDir.DOWN:
                return "above"
            case _:
                return f"the {self.name.lower()}"

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
                l = self.name.lower()
                return l[0] + l[5]
            case ExitDir.INWARDS:
                return "in"
            case ExitDir.OUTWARDS:
                return "out"
            case _:
                return "--"

    @classmethod
    def find(cls, text: str):
        match text.lower():
            case "n" | "north":
                return ExitDir.NORTH
            case "e" | "east":
                return ExitDir.EAST
            case "s" | "south":
                return ExitDir.SOUTH
            case "w" | "west":
                return ExitDir.WEST
            case "nw" | "northwest":
                return ExitDir.NORTHWEST
            case "ne" | "northeast":
                return ExitDir.NORTHEAST
            case "sw" | "southwest":
                return ExitDir.SOUTHWEST
            case "se" | "southeast":
                return ExitDir.SOUTHEAST
            case "i" | "in" | "inwards":
                return ExitDir.INWARDS
            case "o" | "out" | "outwards":
                return ExitDir.OUTWARDS
            case "d" | "down":
                return ExitDir.DOWN
            case "u" | "up":
                return ExitDir.UP
            case _:
                return ExitDir.UNKNOWN

    def delta(self) -> Tuple[float, float, float]:
        match self:
            case ExitDir.NORTH:
                return 0.0, 1.0, 0.0
            case ExitDir.EAST:
                return 1.0, 0.0, 0.0
            case ExitDir.SOUTH:
                return 0.0, -1.0, 0.0
            case ExitDir.WEST:
                return -1.0, 0.0, 0.0
            case ExitDir.UP:
                return 0.0, 0.0, 1.0
            case ExitDir.DOWN:
                return 0.0, 0.0, -1.0
            case ExitDir.NORTHEAST:
                return 1.0, 1.0, 0.0
            case ExitDir.NORTHWEST:
                return -1.0, 1.0, 0.0
            case ExitDir.SOUTHWEST:
                return -1.0, -1.0, 0.0
            case ExitDir.SOUTHEAST:
                return -1.0, 1.0, 0.0
            case _:
                return 0.0, 0.0, 0.0

    def real_direction(self) -> bool:
        match self:
            case ExitDir.INWARDS | ExitDir.OUTWARDS:
                return False
            case _:
                return True


class ExitFlag(IntFlag):
    pass


class MoveType(IntEnum):
    UNKNOWN = -1
    WALK = 0
    FLY = 1
    SWIM = 2
    VEHICLE = 3
    TELEPORT = 4
    INSTANT_TRANSMISSION = 5
    ADMIN_TELEPORT = 6
    SYSTEM_TELEPORT = 7


@dataclass_json
@dataclass(slots=True)
class Exit:
    general_description: Optional[str] = None
    keyword: Optional[str] = None
    exit_info: int = 0
    key: Optional[int] = None
    to_room: Optional[int] = None
    dclock: int = 0
    dchide: int = 0
    dcskill: int = 0
    dcmove: int = 0
    failsavetype: int = 0
    dcfailsave: int = 0
    failroom: Optional[int] = None
    totalfailroom: Optional[int] = None


class ExitDriver:

    __slots__ = ["__weakref__", "destination", "direction", "location", "exit"]

    def __init__(self, exit, location, direction):
        self.exit = exit
        self.direction: ExitDir = direction
        self.destination: Optional[ref["RoomDriver"]] = None
        self.location: Optional[ref["RoomDriver"]] = proxy(location)
        if (dest := snekmud.ROOMS.get(exit.to_room, None)):
            self.destination = proxy(dest)

    async def visible_to(self, character: "CharacterInstanceDriver"):
        return True

    async def can_traverse(self, character: "CharacterInstanceDriver") -> (bool, str):
        return True, ''


class RoomFlag(IntEnum):
    DARK = 0
    DEATH = 1
    NO_MOB = 2
    LIGHT = 3
    PEACEFUL = 4
    SOUNDPROOF = 5
    NO_TRACK = 6
    NO_INSTANT = 7
    TUNNEL = 8
    PRIVATE = 9
    GODROOM = 10
    HOUSE = 11
    HCRSH = 12
    ATRIUM = 13
    OLC = 14
    ASTERISK = 15
    VEHICLE = 16
    UNDERGROUND = 17
    CURRENT = 18
    TIMED_DT = 19
    EARTH = 20
    VEGETA = 21
    FRIGID = 22
    KONACK = 23
    NAMEK = 24
    NEO = 25
    AL = 26
    SPACE = 27
    PUNISHMENT_HALL = 28
    REGEN = 29
    HELL = 30
    GRAV_X10 = 31
    AETHER = 32
    HBTC = 33
    PAST = 34
    CBANK = 35
    SHIP = 36
    YARDRAT = 37
    KANASSA = 38
    ARLIA = 39
    AURA = 40
    EARTHORB = 41
    FRIGIDOR = 42
    KONACKOR = 43
    NAMEKORB = 44
    VEGETAOR = 45
    AETHEROR = 46
    YARDRAOR = 47
    KANASSOR = 48
    ARLIAORB = 49
    NEBULA = 50
    ASTEROID = 51
    WORMHOLE = 52
    SSTATION = 53
    ISSTAR = 54
    CERRIA = 55
    CERORBIT = 56
    BEDROOM = 57
    WORKOUT = 58
    GARDEN = 59
    GREENHOUSE = 60
    FERTILE1 = 61
    FERTILE2 = 62
    FISHING = 63
    FRESHWATFISH = 64
    CANREMODEL = 65

    def is_legacy_planet(self) -> bool:
        match self:
            case RoomFlag.EARTH | RoomFlag.FRIGID | RoomFlag.KONACK | RoomFlag.NAMEK | RoomFlag.VEGETA | \
                 RoomFlag.AETHER | RoomFlag.YARDRAT | RoomFlag.KANASSA | RoomFlag.ARLIA | RoomFlag.CERRIA:
                return True
        return False

    def is_legacy_orbit(self) -> bool:
        match self:
            case RoomFlag.EARTHORB | RoomFlag.FRIGIDOR | RoomFlag.KONACKOR | RoomFlag.NAMEKORB | RoomFlag.VEGETAOR | \
                 RoomFlag.AETHEROR | RoomFlag.YARDRAOR | RoomFlag.KANASSOR | RoomFlag.ARLIAORB | RoomFlag.CERORBIT:
                return True
        return False


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


def decode_exits(data):
    return {ExitDir(k): Exit.from_dict(v) for k, v in data}


def encode_exits(data):
    return [(k, v) for k, v in data.items()]


@dataclass_json
@dataclass(slots=True)
class Room:
    vnum: int = -1
    sector_type: SectorType = SectorType.UNKNOWN
    name: str = "New Room"
    description: str = "No description yet."
    ex_description: Dict[str, str] = field(default_factory=dict)
    room_flags: List[RoomFlag] = field(default_factory=list)
    exits: Dict[ExitDir, Exit] = field(default_factory=dict, metadata=config(decoder=decode_exits,
                                                                             encoder=encode_exits,
                                                                             mm_field=fields.Raw()))
    triggers: List[int] = field(default_factory=list)


class RoomDriver:

    __slots__ = ["__weakref__", "room", "exits", "objects", "characters", "entrances", "gravity",
                 "dmg", "geffect", "zone"]

    def __init__(self, room, zone):
        self.room = room
        self.zone = zone
        self.exits: Dict[ExitDir, ExitDriver] = dict()
        self.objects: WeakSet["Object"] = WeakSet()
        self.characters: WeakSet["CharacterInstanceDriver"] = WeakSet()
        self.entrances: WeakValueDictionary[ExitDir, ref["Exit"]] = WeakValueDictionary()
        self.gravity = 1
        self.dmg = 0
        self.geffect = 0

    async def character_leave(self, character: "CharacterInstanceDriver"):
        self.characters.remove(character)

    async def character_enter(self, character: "CharacterInstanceDriver"):
        self.characters.add(character)

    async def setup(self):
        exit_driver = snekmud.CLASSES["exit_driver"]
        for k, v in self.room.exits.items():
            self.exits[k] = exit_driver(v, self, k)

    def to_dict(self):
        return self.entity.to_dict()

    def to_json(self):
        return self.entity.to_json()

    def get_other_characters(self, character):
        inhab = set(self.characters)
        if character in inhab:
            inhab.remove(character)
        return inhab

    def get_gravity_fancy(self):
        match self.gravity:
            case 1:
                return "Normal"
            case _:
                return f"{self.gravity}x"

    @property
    def entity(self):
        return self.room
