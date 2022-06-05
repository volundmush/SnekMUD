from typing import List, Optional, Dict, Union, Set, Tuple
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum

# DO NOT GLOBAL IMPORT ANYTHING FROM MUDFORGE OR SNEKMUD IN THIS FILE. It's only for defining
# data. We don't want to cause circular imports.


class Size(IntEnum):
    UNDEFINED = -1
    FINE = 0
    DIMINUTIVE = 1
    TINY = 2
    SMALL = 3
    MEDIUM = 4
    LARGE = 5
    HUGE = 6
    GARGANTUAN = 7
    COLOSSAL = 8

    def __str__(self):
        return self.name.capitalize()


class Sex(IntEnum):
    NEUTER = 0
    MALE = 1
    FEMALE = 2
    OTHER = 3

    def __str__(self):
        return self.name.capitalize()

    def subjective(self):
        match self:
            case Sex.NEUTER:
                return "it"
            case Sex.MALE:
                return "he"
            case Sex.FEMALE:
                return "she"
            case Sex.OTHER | _:
                return "they"

    def objective(self):
        match self:
            case Sex.NEUTER:
                return "it"
            case Sex.MALE:
                return "him"
            case Sex.FEMALE:
                return "her"
            case Sex.OTHER | _:
                return "them"

    def possessive(self):
        match self:
            case Sex.NEUTER:
                return "its"
            case Sex.MALE:
                return "his"
            case Sex.FEMALE:
                return "hers"
            case Sex.OTHER | _:
                return "their"

    def absolute(self):
        match self:
            case Sex.NEUTER:
                return "its"
            case Sex.MALE:
                return "his"
            case Sex.FEMALE:
                return "her"
            case Sex.OTHER | _:
                return "theirs"


class Alignment(IntEnum):
    SAINTLY = 0
    VALIANT = 1
    HERO = 2
    DO_GOODER = 3
    NEUTRAL = 4
    CROOK = 5
    VILLAIN = 6
    TERRIBLE = 7
    HORRIBLY_EVIL = 8

    def __str__(self):
        match self:
            case Alignment.DO_GOODER:
                return "Do-gooder"
            case Alignment.HORRIBLY_EVIL:
                return "Horribly Evil"
            case _:
                return self.name.capitalize()


class ForeheadAppendage(IntEnum):
    STUBBY = 0
    SHORT = 1
    MEDIUM = 2
    LONG = 3
    REALLY_LONG = 4

    def __str__(self):
        match self:
            case ForeheadAppendage.REALLY_LONG:
                return "really long"
            case _:
                return self.name.lower()


class AuraColor(IntEnum):
    WHITE = 0
    BLUE = 1
    RED = 2
    GREEN = 3
    PINK = 4
    PURPLE = 5
    YELLOW = 6
    BLACK = 7
    ORANGE = 8

    def __str__(self):
        return self.name.lower()


class EyeColor(IntEnum):
    BLUE = 0
    BLACK = 1
    GREEN = 2
    BROWN = 3
    RED = 4
    AQUA = 5
    PINK = 6
    PURPLE = 7
    CRIMSON = 8
    GOLD = 9
    AMBER = 10
    EMERALD = 11

    def __str__(self):
        return self.name.lower()


class HairLength(IntEnum):
    BALD = 0
    SHORT = 1
    MEDIUM = 2
    LONG = 3
    REALLY_LONG = 4

    def __str__(self):
        return self.name.lower()


class HairColor(IntEnum):
    HEADED = 0
    BLACK = 1
    BROWN = 2
    BLONDE = 3
    GREY = 4
    RED = 5
    ORANGE = 6
    GREEN = 7
    BLUE = 8
    PINK = 9
    PURPLE = 10
    SILVER = 11
    CRIMSON = 12
    WHITE = 13

    def __str__(self):
        return self.name.lower()


class HairStyle(IntEnum):
    UNKNOWN = 0
    PLAIN = 1
    MOHAWK = 2
    SPIKY = 3
    CURLY = 4
    UNEVEN = 5
    PONYTAIL = 6
    AFRO = 7
    FADE = 8
    CREW_CUT = 9
    FEATHERED = 10
    DREAD_LOCKS = 11

    def __str__(self):
        match self:
            case HairStyle.DREAD_LOCKS:
                return "dread locks"
            case HairStyle.CREW_CUT:
                return "crew cut"
            case _:
                return self.name.lower()

    def describe(self):
        match self:
            case HairStyle.PLAIN:
                return "with a plain look"
            case HairStyle.MOHAWK:
                return "in a mohawk"
            case HairStyle.SPIKY:
                return "with a spiky look"
            case HairStyle.CURLY:
                return "with a curly look"
            case HairStyle.UNEVEN:
                return "with an uneven look"
            case HairStyle.PONYTAIL:
                return "in a ponytail"
            case HairStyle.AFRO:
                return "in an afro"
            case HairStyle.FADE:
                return "with a fade look"
            case HairStyle.CREW_CUT:
                return "in a crew cut"
            case HairStyle.FEATHERED:
                return "with a feathered look"
            case HairStyle.DREAD_LOCKS:
                return "in dread locks"
            case _:
                return "in enigmatic form"


class SkinColor(IntEnum):
    WHITE = 0
    BLACK = 1
    GREEN = 2
    ORANGE = 3
    YELLOW = 4
    RED = 5
    GREY = 6
    BLUE = 7
    AQUA = 8
    PINK = 9
    PURPLE = 10
    TAN = 11

    def __str__(self):
        return self.name.lower()


class DistinguishingFeature(IntEnum):
    EYE = 0
    HAIR = 1
    SKIN = 2
    HEIGHT = 3
    WEIGHT = 4


class Position(IntEnum):
    DEAD = 0
    MORTALLY_WOUNDED = 1
    INCAPACITATED = 2
    STUNNED = 3
    SLEEPING = 4
    RESTING = 5
    SITTING = 6
    FIGHTING = 7
    STANDING = 8


class WearFlag(IntFlag):
    pass


class ExtraFlag(IntFlag):
    pass


class ObjectFlag(IntFlag):
    pass


class EntityType(IntEnum):
    JUNK = 0
    ITEM = 1
    CHARACTER = 2
    CELESTIAL_BODY = 3
    REGION = 4
    STRUCTURE = 5
    VEHICLE = 6
    SECTOR = 7

    def __str__(self):
        return self.name.lower()

    def get_proto_class(self):
        import snekmud
        return snekmud.PROTOTYPE_CLASSES.get(str(self), None)

    def instance_class(self):
        import snekmud
        return snekmud.INSTANCE_CLASSES.get(str(self), None)


class ObjectType(IntEnum):
    JUNK = 0
    LIGHT = 1
    SCROLL = 2
    WAND = 3
    STAFF = 4
    WEAPON = 5
    FIREWEAPON = 6
    CAMPFIRE = 7
    TREASURE = 8
    ARMOR = 9
    POTION = 10
    WORN = 11
    OTHER = 12
    TRASH = 13
    TRAP = 14
    CONTAINER = 15
    NOTE = 16
    DRINKCON = 17
    KEY = 18
    FOOD = 19
    MONEY = 20
    PEN = 21
    BOAT = 22
    FOUNTAIN = 23
    VEHICLE = 24
    HATCH = 25
    WINDOW = 26
    CONTROL = 27
    PORTAL = 28
    SPELLBOOK = 29
    BOARD = 30
    CHAIR = 31
    BED = 32
    YUM = 33
    PLANT = 34
    FISHPOLE = 35
    FISHBAIT = 36


class LocationType(IntEnum):
    INVENTORY = 0
    EQUIPMENT = 1
    MAP = 2
    SPACE = 3





Coordinates = Tuple[float, float, float]
NewLocation = Tuple[str, str, LocationType, Coordinates]
Location = Union[None, int, NewLocation]
