from typing import List, Optional, Dict
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum
from snekmud.db.misc import Size


class RaceId(IntEnum):
    UNKNOWN = -1
    HUMAN = 0
    SAIYAN = 1
    ICER = 2
    KONATSU = 3
    NAMEKIAN = 4
    MUTANT = 5
    KANASSAN = 6
    HALFBREED = 7
    BIO = 8
    ANDROID = 9
    DEMON = 10
    MAJIN = 11
    KAI = 12
    TRUFFLE = 13
    HOSHIJIN = 14
    ANIMAL = 15
    SAIBA = 16
    SERPENT = 17
    OGRE = 18
    YARDRATIAN = 19
    ARLIAN = 20
    DRAGON = 21
    MECHANICAL = 22
    SPIRIT = 23


class BaseRace:
    race_id = RaceId.UNKNOWN
    name = "Unknown"
    abbr = "???"
    size = Size.MEDIUM
    player_race = False


class PlayerRace(BaseRace):
    player_race = True


class Human(PlayerRace):
    race_id = RaceId.HUMAN
    name = "Human"
    abbr = "Hum"


class Saiyan(PlayerRace):
    race_id = RaceId.SAIYAN
    name = "Saiyan"
    abbr = "Sai"


class Icer(PlayerRace):
    race_id = RaceId.ICER
    name = "Icer"
    abbr = "Ice"


class Konatsu(PlayerRace):
    race_id = RaceId.KONATSU
    name = "Konatsu"
    abbr = "Kon"


class Namekian(PlayerRace):
    race_id = RaceId.NAMEKIAN
    name = "Namekian"
    abbr = "Nam"


class Mutant(PlayerRace):
    race_id = RaceId.MUTANT
    name = "Mutant"
    abbr = "Mut"


class Kanassan(PlayerRace):
    race_id = RaceId.KANASSAN
    name = "Kanassan"
    abbr = "Kan"


class Halfbreed(PlayerRace):
    race_id = RaceId.HALFBREED
    name = "Halfbreed"
    abbr = "H-B"


class BioAndroid(PlayerRace):
    race_id = RaceId.BIO
    name = "BioAndroid"
    abbr = "Bio"


class Android(PlayerRace):
    race_id = RaceId.ANDROID
    name = "Android"
    abbr = "And"


class Demon(PlayerRace):
    race_id = RaceId.DEMON
    name = "Demon"
    abbr = "Dem"


class Majin(PlayerRace):
    race_id = RaceId.MAJIN
    name = "Majin"
    abbr = "Maj"


class Kai(PlayerRace):
    race_id = RaceId.KAI
    name = "Kai"
    abbr = "Kai"


class Truffle(PlayerRace):
    race_id = RaceId.TRUFFLE
    name = "Truffle"
    abbr = "Tru"
    size = Size.SMALL


class Hoshijin(PlayerRace):
    race_id = RaceId.HOSHIJIN
    name = "Hoshijin"
    abbr = "Hos"


class Animal(BaseRace):
    race_id = RaceId.ANIMAL
    name = "Animal"
    abbr = "Ani"
    size = Size.FINE


class Saiba(BaseRace):
    race_id = RaceId.SAIBA
    name = "Saiba"
    abbr = "Sab"
    size = Size.LARGE


class Serpent(BaseRace):
    race_id = RaceId.SERPENT
    name = "Serpent"
    abbr = "Ser"


class Ogre(BaseRace):
    race_id = RaceId.OGRE
    name = "Ogre"
    abbr = "Ogr"
    size = Size.LARGE


class Yardratian(BaseRace):
    race_id = RaceId.YARDRATIAN
    name = "Yardratian"
    abbr = "Yar"


class Arlian(PlayerRace):
    race_id = RaceId.ARLIAN
    name = "Arlian"
    abbr = "Arl"


class Dragon(BaseRace):
    race_id = RaceId.DRAGON
    name = "Dragon"
    abbr = "Drg"


class Mechanical(BaseRace):
    race_id = RaceId.MECHANICAL
    name = "Mechanical"
    abbr = "Mec"


class Spirit(BaseRace):
    race_id = RaceId.SPIRIT
    name = "Spirit"
    abbr = "Spi"
    size = Size.TINY

ALL_RACES = [Human, Saiyan, Icer, Konatsu, Namekian, Mutant, Kanassan, Halfbreed,
             BioAndroid, Android, Demon, Majin, Kai, Truffle, Hoshijin, Animal,
             Saiba, Serpent, Ogre, Yardratian, Arlian, Dragon, Mechanical, Spirit]

RACE_MAP = {r.race_id: r for r in ALL_RACES}