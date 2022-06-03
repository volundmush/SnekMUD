from typing import List, Optional, Dict
from weakref import WeakValueDictionary, ref, WeakSet
from rich.text import Text
from enum import IntFlag, IntEnum


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


class Sex(IntEnum):
    NEUTER = 0
    MALE = 1
    FEMALE = 2
    OTHER = 3


class Exportable:
    direct_fields = []
    rich_fields = []

    __slots__ = ["__weakref__", ]

    def export(self) -> dict:
        base = {k: getattr(self, k) for k in self.direct_fields}
        for f in self.rich_fields:
            base[f] = getattr(self, f).serialize()
        return base

    def load(self, data: dict):
        for k, v in data.items():
            if k not in self.direct_fields and k not in self.rich_fields:
                continue
            if k in self.rich_fields:
                v = Text.deserialize(v)
            setattr(self, k, v)