from typing import List, Optional, Dict
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum

class SenseiId(IntEnum):
    COMMONER = -1
    ROSHI = 0
    PICCOLO = 1
    KRANE = 2
    NAIL = 3
    BARDOCK = 4
    GINYU = 5
    FRIEZA = 6
    TAPION = 7
    SIXTEEN = 8
    DABURA = 9
    KIBITO = 10
    JINTO = 11
    TSUNA = 12
    KURZAK = 13


class BaseSensei:
    sensei_id = SenseiId.COMMONER
    name = "Commoner"
    abbr = "Co"


class Roshi(BaseSensei):
    sensei_id = SenseiId.ROSHI
    name = "Roshi"
    abbr = "Ro"


class Piccolo(BaseSensei):
    sensei_id = SenseiId.PICCOLO
    name = "Piccolo"
    abbr = "Pi"


class Krane(BaseSensei):
    sensei_id = SenseiId.KRANE
    name = "Krane"
    abbr = "Kr"


class Nail(BaseSensei):
    sensei_id = SenseiId.NAIL
    name = "Nail"
    abbr = "Na"


class Bardock(BaseSensei):
    sensei_id = SenseiId.BARDOCK
    name = "Bardock"
    abbr = "Ba"


class Ginyu(BaseSensei):
    sensei_id = SenseiId.GINYU
    name = "Ginyu"
    abbr = "Gi"

class Frieza(BaseSensei):
    sensei_id = SenseiId.FRIEZA
    name = "Frieza"
    abbr = "Fr"

class Tapion(BaseSensei):
    sensei_id = SenseiId.TAPION
    name = "Tapion"
    abbr = "Ta"


class Sixteen(BaseSensei):
    sensei_id = SenseiId.SIXTEEN
    name = "Sixteen"
    abbr = "16"


class Dabura(BaseSensei):
    sensei_id = SenseiId.DABURA
    name = "Dabura"
    abbr = "Da"


class Kibito(BaseSensei):
    sensei_id = SenseiId.KIBITO
    name = "Kibito"
    abbr = "Ki"


class Jinto(BaseSensei):
    sensei_id = SenseiId.JINTO
    name = "Jinto"
    abbr = "Ji"


class Tsuna(BaseSensei):
    sensei_id = SenseiId.TSUNA
    name = "Tsuna"
    abbr = "Ts"


class Kurzak(BaseSensei):
    sensei_id = SenseiId.KURZAK
    name = "Kurzak"
    abbr = "Ku"

ALL_SENSEI = [Roshi, Piccolo, Krane, Nail, Bardock, Ginyu, Frieza, Tapion,
              Sixteen, Dabura, Kibito, Jinto, Tsuna, Kurzak]

SENSEI_MAP = {s.sensei_id: s for s in ALL_SENSEI}